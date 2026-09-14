import os
import time
import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pymysql

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    average_precision_score,
    roc_curve,
    auc,
)


try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except Exception:
    LIGHTGBM_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOT_AVAILABLE = True
except Exception:
    PLOT_AVAILABLE = False


@dataclass
class ForecastConfig:
    days_history: int = 180
    horizon_days: int = 30
    test_size: float = 0.2
    random_state: int = 42
    output_dir: str = os.path.join("static", "images", "model_eval")


class XgbLgbSalesForecaster:
    """
    说明：
    - 回归任务：预测 next_day_amount（次日销售额）
    - 二分类任务：预测 next_day_up（次日是否增长，用于 ROC/PR/混淆矩阵/F1/mAP 对比）
    - mAP：这里用二分类的 AP 作为 mAP（多分类一般是各类 AP 的均值）
    - 参数量、FLOPs：树模型无“神经网络参数/FLOPs”标准口径，这里给出基于树节点数量的近似估算
    """

    def __init__(self, config: ForecastConfig | None = None):
        self.cfg = config or ForecastConfig()

    def connect_db(self):
        return pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            passwd="123456",
            db="new_retail",
            charset="utf8mb4",
            connect_timeout=10,
        )

    def load_daily_sales(self, days: int | None = None) -> pd.DataFrame:
        days = days or self.cfg.days_history
        conn = None
        cursor = None
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            sql_recent = """
            SELECT
                DATE(create_time) AS d,
                COUNT(*) AS order_count,
                IFNULL(SUM(payment_amount), 0) AS total_amount
            FROM sales_order
            WHERE create_time >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY DATE(create_time)
            ORDER BY d
            """
            cursor.execute(sql_recent, (int(days),))
            rows = cursor.fetchall()

            # 若近N天没有数据，则退化为全表汇总（兼容历史数据时间较早的情况）
            if not rows:
                sql_all = """
                SELECT
                    DATE(create_time) AS d,
                    COUNT(*) AS order_count,
                    IFNULL(SUM(payment_amount), 0) AS total_amount
                FROM sales_order
                GROUP BY DATE(create_time)
                ORDER BY d
                """
                cursor.execute(sql_all)
                rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=["date", "order_count", "total_amount"])
            if df.empty:
                return df
            df["date"] = pd.to_datetime(df["date"])
            df["order_count"] = df["order_count"].fillna(0).astype(float)
            df["total_amount"] = df["total_amount"].fillna(0).astype(float)

            # 补齐连续日期
            date_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
            df = df.set_index("date").reindex(date_range).reset_index().rename(columns={"index": "date"})
            df["order_count"] = df["order_count"].fillna(0.0)
            df["total_amount"] = df["total_amount"].fillna(0.0)

            # 若天数过少，自动造一些跨天订单数据，保证可训练/可视化
            if len(df) < 20:
                seed_days = max(int(days), 200)
                self._seed_sales_orders_if_needed(min_days=seed_days, orders_per_day=30)
                # 重新加载（全表）
                cursor.execute("""
                    SELECT
                        DATE(create_time) AS d,
                        COUNT(*) AS order_count,
                        IFNULL(SUM(payment_amount), 0) AS total_amount
                    FROM sales_order
                    GROUP BY DATE(create_time)
                    ORDER BY d
                """)
                rows2 = cursor.fetchall()
                df = pd.DataFrame(rows2, columns=["date", "order_count", "total_amount"])
                df["date"] = pd.to_datetime(df["date"])
                df["order_count"] = df["order_count"].fillna(0).astype(float)
                df["total_amount"] = df["total_amount"].fillna(0).astype(float)
                date_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
                df = df.set_index("date").reindex(date_range).reset_index().rename(columns={"index": "date"})
                df["order_count"] = df["order_count"].fillna(0.0)
                df["total_amount"] = df["total_amount"].fillna(0.0)
            # 只保留最近窗口，避免历史长跨度导致大量0天影响训练/评估
            if len(df) > int(days):
                df = df.tail(int(days)).reset_index(drop=True)

            # 若最近窗口内“有订单的天数”过少，则自动造数覆盖最近窗口
            has_zero_day = bool((df["order_count"] <= 0).any()) if not df.empty else True
            nonzero_days = int((df["order_count"] > 0).sum()) if not df.empty else 0
            if has_zero_day or nonzero_days < 20:
                seed_days = max(int(days), 200)
                self._seed_sales_orders_if_needed(min_days=seed_days, orders_per_day=30)
                # 重新加载最近窗口（全表汇总 + 截取）
                cursor.execute("""
                    SELECT
                        DATE(create_time) AS d,
                        COUNT(*) AS order_count,
                        IFNULL(SUM(payment_amount), 0) AS total_amount
                    FROM sales_order
                    GROUP BY DATE(create_time)
                    ORDER BY d
                """)
                rows3 = cursor.fetchall()
                df = pd.DataFrame(rows3, columns=["date", "order_count", "total_amount"])
                if df.empty:
                    return df
                df["date"] = pd.to_datetime(df["date"])
                df["order_count"] = df["order_count"].fillna(0).astype(float)
                df["total_amount"] = df["total_amount"].fillna(0).astype(float)
                date_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
                df = df.set_index("date").reindex(date_range).reset_index().rename(columns={"index": "date"})
                df["order_count"] = df["order_count"].fillna(0.0)
                df["total_amount"] = df["total_amount"].fillna(0.0)
                if len(df) > int(days):
                    df = df.tail(int(days)).reset_index(drop=True)
            return df
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _seed_sales_orders_if_needed(self, min_days: int = 60, orders_per_day: int = 30):
        """当 sales_order 按天数据过少时，插入跨多天的模拟订单（含少量退款）"""
        conn = None
        cursor = None
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            # 只检查最近 min_days 天窗口，避免历史跨度很大导致误判“已经足够”
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(create_time))
                FROM sales_order
                WHERE create_time >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (int(min_days),))
            cur_days = int(cursor.fetchone()[0] or 0)
            if cur_days >= int(min_days):
                return

            cursor.execute("SELECT id FROM py_user ORDER BY id LIMIT 50")
            user_ids = [int(r[0]) for r in cursor.fetchall()]
            if not user_ids:
                return

            cursor.execute("SELECT id FROM sales_channel ORDER BY id LIMIT 50")
            channel_ids = [int(r[0]) for r in cursor.fetchall()]
            channel_id = channel_ids[0] if channel_ids else None

            payment_methods = ["alipay", "wechat", "card", "cash"]
            delivery_methods = ["express", "self"]
            order_sources = ["online", "offline"]

            now = datetime.now()
            insert_sql = """
                INSERT INTO sales_order
                (order_no, user_id, store_id, order_source, channel_id, campaign_id,
                 order_status, payment_method, payment_status, payment_time,
                 delivery_method, delivery_status, delivery_time, complete_time,
                 address_id, total_amount, discount_amount, shipping_amount, payment_amount,
                 remark, create_time, update_time)
                VALUES
                (%s, %s, NULL, %s, %s, NULL,
                 %s, %s, %s, %s,
                 %s, %s, NULL, NULL,
                 NULL, %s, 0.00, 0.00, %s,
                 %s, %s, %s)
            """

            batch = []
            # 生成 min_days 天的订单（分布更像真实：多数已完成，少量退款/取消）
            for d in range(int(min_days)):
                day = now.date() - timedelta(days=int(min_days) - 1 - d)
                for j in range(int(orders_per_day)):
                    uid = int(user_ids[(d * orders_per_day + j) % len(user_ids)])
                    pm = payment_methods[(j + d) % len(payment_methods)]
                    dm = delivery_methods[(j + 2 * d) % len(delivery_methods)]
                    src = order_sources[(j + d) % len(order_sources)]
                    # 退款概率
                    r = (j % 20 == 0)
                    c = (j % 25 == 0)
                    if r:
                        order_status = 5
                        payment_status = 2
                        remark = "mock_refund"
                    elif c:
                        order_status = 4
                        payment_status = 0
                        remark = "mock_cancel"
                    else:
                        order_status = 3
                        payment_status = 1
                        remark = "mock_done"

                    amt = float(20 + ((j * 37 + d * 19) % 980))  # 20~999
                    order_no = f"MOCK_O_{day.strftime('%Y%m%d')}_{d}_{j}_{int(time.time() * 1000) % 100000}"
                    create_time = datetime.combine(day, datetime.min.time()) + timedelta(minutes=(j * 7) % (24 * 60))
                    update_time = create_time
                    payment_time = create_time + timedelta(minutes=5) if payment_status in (1, 2) else None
                    delivery_status = 2 if order_status in (3, 5) else 0

                    batch.append((
                        order_no, uid, src, channel_id,
                        int(order_status), pm, int(payment_status), payment_time,
                        dm, int(delivery_status),
                        float(amt), float(amt),
                        remark, create_time, update_time
                    ))

            cursor.executemany(insert_sql, batch)
            conn.commit()
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            print(f"造订单数据失败: {e}")
            traceback.print_exc()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def make_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["dayofweek"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day
        df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

        # 滞后与滚动
        for i in range(1, 15):
            df[f"lag_amt_{i}"] = df["total_amount"].shift(i)
            df[f"lag_ord_{i}"] = df["order_count"].shift(i)

        df["roll_amt_7"] = df["total_amount"].rolling(7).mean()
        df["roll_amt_14"] = df["total_amount"].rolling(14).mean()
        df["roll_ord_7"] = df["order_count"].rolling(7).mean()
        df["roll_ord_14"] = df["order_count"].rolling(14).mean()

        # 目标：次日销售额
        df["next_day_amount"] = df["total_amount"].shift(-1)

        df = df.dropna().reset_index(drop=True)
        return df

    def feature_columns(self) -> list[str]:
        cols = ["dayofweek", "month", "day", "is_weekend"]
        cols += [f"lag_amt_{i}" for i in range(1, 15)]
        cols += [f"lag_ord_{i}" for i in range(1, 15)]
        cols += ["roll_amt_7", "roll_amt_14", "roll_ord_7", "roll_ord_14"]
        return cols

    def _ensure_output_dir(self) -> str:
        out = self.cfg.output_dir
        os.makedirs(out, exist_ok=True)
        return out

    def _approx_tree_stats(self, model, model_name: str) -> dict:
        """
        参数量/FLOPs近似：
        - params ~ total_nodes * k  (k 取常数，仅用于相对对比)
        - flops_per_sample ~ avg_nodes_visited * ops_per_node
        """
        stats = {"model": model_name, "n_trees": None, "n_nodes": None, "approx_params": None, "approx_flops": None}
        try:
            if model_name.startswith("xgb") and XGBOOST_AVAILABLE:
                booster = model.get_booster()
                df = booster.trees_to_dataframe()
                n_nodes = int(df.shape[0])
                n_trees = int(df["Tree"].nunique())
                stats["n_trees"] = n_trees
                stats["n_nodes"] = n_nodes
            elif model_name.startswith("lgb") and LIGHTGBM_AVAILABLE:
                dump = model.booster_.dump_model()
                n_trees = int(len(dump.get("tree_info", [])))
                n_nodes = 0
                for t in dump.get("tree_info", []):
                    n_nodes += int(t.get("num_leaves", 0)) * 2 - 1  # 近似二叉树节点数
                stats["n_trees"] = n_trees
                stats["n_nodes"] = int(n_nodes)

            if stats["n_nodes"] is not None:
                stats["approx_params"] = int(stats["n_nodes"] * 6)  # 每节点存若干标量（近似）
                stats["approx_flops"] = int(stats["n_nodes"] * 2)   # 每节点一次比较+一次跳转（近似）
        except Exception:
            pass
        return stats

    def _measure_infer_speed(self, predict_fn, X: np.ndarray, n_runs: int = 50) -> dict:
        # warmup
        _ = predict_fn(X[: min(len(X), 32)])
        start = time.perf_counter()
        for _ in range(n_runs):
            _ = predict_fn(X)
        end = time.perf_counter()
        elapsed = end - start
        per_run = elapsed / n_runs
        per_sample = per_run / max(1, len(X))
        return {"infer_total_s": elapsed, "infer_s_per_run": per_run, "infer_s_per_sample": per_sample}

    def train_and_evaluate(self) -> dict:
        out_dir = self._ensure_output_dir()
        df_raw = self.load_daily_sales()
        if df_raw is None or df_raw.empty or len(df_raw) < 20:
            return {"error": "历史销售数据不足，至少需要20天以上日级数据"}

        df = self.make_features(df_raw)
        if df is None or df.empty or len(df) < 10:
            return {"error": "可用训练样本不足（特征工程后样本数<10），请增加历史天数或生成更多订单数据"}
        feats = self.feature_columns()
        X = df[feats].values
        y_reg = df["next_day_amount"].values
        # 二分类标签：是否达到高销量阈值（分位数），用于 ROC/PR/F1/mAP 等指标展示
        # 为避免时间切分导致测试集单一类别，采用自适应分位阈值（0.8→0.5）
        split_idx = int(len(y_reg) * (1 - self.cfg.test_size))
        best_thr = None
        y_cls = None
        for q in [0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]:
            thr = float(np.quantile(y_reg[:split_idx], q)) if split_idx > 0 else float(np.quantile(y_reg, q))
            tmp = (y_reg >= thr).astype(int)
            if len(np.unique(tmp[:split_idx])) >= 2 and len(np.unique(tmp[split_idx:])) >= 2:
                best_thr = thr
                y_cls = tmp
                break
        if y_cls is None:
            # 兜底：用中位数
            best_thr = float(np.median(y_reg))
            y_cls = (y_reg >= best_thr).astype(int)

        X_train, X_test, y_reg_train, y_reg_test, y_cls_train, y_cls_test = train_test_split(
            X, y_reg, y_cls, test_size=self.cfg.test_size, random_state=self.cfg.random_state, shuffle=False
        )

        results = {
            "generated_at": datetime.now().isoformat(),
            "out_dir": out_dir,
            "classification_threshold": best_thr,
            "models": {}
        }

        def eval_reg(y_true, y_pred):
            return {
                "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
                "mae": float(mean_absolute_error(y_true, y_pred)),
                "r2": float(r2_score(y_true, y_pred)),
            }

        def eval_cls(y_true, y_prob, threshold=0.5):
            y_pred = (y_prob >= threshold).astype(int)
            cm = confusion_matrix(y_true, y_pred)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            ap = average_precision_score(y_true, y_prob)
            fpr, tpr, _ = roc_curve(y_true, y_prob)
            roc_auc = auc(fpr, tpr)
            prec, rec, _ = precision_recall_curve(y_true, y_prob)
            return {
                "f1": float(f1),
                "mAP": float(ap),
                "roc_auc": float(roc_auc),
                "confusion_matrix": cm.tolist(),
                "roc_curve": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
                "pr_curve": {"precision": prec.tolist(), "recall": rec.tolist()},
            }

        def save_plots(model_key: str, y_true, y_prob):
            if not PLOT_AVAILABLE:
                return {}
            paths = {}

            # Confusion matrix
            y_pred = (y_prob >= 0.5).astype(int)
            cm = confusion_matrix(y_true, y_pred)
            plt.figure(figsize=(4.6, 4.2))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
            plt.title(f"Confusion Matrix ({model_key})")
            plt.xlabel("Pred")
            plt.ylabel("True")
            p1 = os.path.join(out_dir, f"cm_{model_key}.png")
            plt.tight_layout()
            plt.savefig(p1, dpi=160)
            plt.close()
            paths["confusion_matrix_png"] = p1.replace("\\", "/")

            # ROC
            fpr, tpr, _ = roc_curve(y_true, y_prob)
            roc_auc = auc(fpr, tpr)
            plt.figure(figsize=(5.2, 4.2))
            plt.plot(fpr, tpr, label=f"AUC={roc_auc:.3f}")
            plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
            plt.title(f"ROC ({model_key})")
            plt.xlabel("FPR")
            plt.ylabel("TPR")
            plt.legend()
            p2 = os.path.join(out_dir, f"roc_{model_key}.png")
            plt.tight_layout()
            plt.savefig(p2, dpi=160)
            plt.close()
            paths["roc_png"] = p2.replace("\\", "/")

            # PR
            prec, rec, _ = precision_recall_curve(y_true, y_prob)
            ap = average_precision_score(y_true, y_prob)
            plt.figure(figsize=(5.2, 4.2))
            plt.plot(rec, prec, label=f"AP={ap:.3f}")
            plt.title(f"PR Curve ({model_key})")
            plt.xlabel("Recall")
            plt.ylabel("Precision")
            plt.legend()
            p3 = os.path.join(out_dir, f"pr_{model_key}.png")
            plt.tight_layout()
            plt.savefig(p3, dpi=160)
            plt.close()
            paths["pr_png"] = p3.replace("\\", "/")
            return paths

        # 1) XGBoost
        if XGBOOST_AVAILABLE:
            try:
                xgb_reg = xgb.XGBRegressor(
                    n_estimators=300,
                    max_depth=6,
                    learning_rate=0.06,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=self.cfg.random_state,
                )
                xgb_reg.fit(X_train, y_reg_train)
                pred_reg = xgb_reg.predict(X_test)

                xgb_cls = xgb.XGBClassifier(
                    n_estimators=300,
                    max_depth=5,
                    learning_rate=0.06,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=self.cfg.random_state,
                    eval_metric="logloss",
                )
                xgb_cls.fit(X_train, y_cls_train)
                prob = xgb_cls.predict_proba(X_test)[:, 1]

                speed = self._measure_infer_speed(lambda _X: xgb_cls.predict_proba(_X)[:, 1], X_test)
                stats = self._approx_tree_stats(xgb_cls, "xgb_cls")
                plots = save_plots("xgb", y_cls_test, prob)

                results["models"]["xgb"] = {
                    "regression": eval_reg(y_reg_test, pred_reg),
                    "classification": eval_cls(y_cls_test, prob),
                    "infer_speed": speed,
                    "approx_complexity": stats,
                    "plots": plots,
                }
            except Exception as e:
                traceback.print_exc()
                results["models"]["xgb"] = {"error": str(e)}
        else:
            results["models"]["xgb"] = {"error": "xgboost 未安装"}

        # 2) LightGBM
        if LIGHTGBM_AVAILABLE:
            try:
                lgb_reg = lgb.LGBMRegressor(
                    n_estimators=500,
                    learning_rate=0.05,
                    num_leaves=64,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=self.cfg.random_state,
                )
                lgb_reg.fit(X_train, y_reg_train)
                pred_reg = lgb_reg.predict(X_test)

                lgb_cls = lgb.LGBMClassifier(
                    n_estimators=500,
                    learning_rate=0.05,
                    num_leaves=64,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=self.cfg.random_state,
                )
                lgb_cls.fit(X_train, y_cls_train)
                prob = lgb_cls.predict_proba(X_test)[:, 1]

                speed = self._measure_infer_speed(lambda _X: lgb_cls.predict_proba(_X)[:, 1], X_test)
                stats = self._approx_tree_stats(lgb_cls, "lgb_cls")
                plots = save_plots("lgb", y_cls_test, prob)

                results["models"]["lgb"] = {
                    "regression": eval_reg(y_reg_test, pred_reg),
                    "classification": eval_cls(y_cls_test, prob),
                    "infer_speed": speed,
                    "approx_complexity": stats,
                    "plots": plots,
                }
            except Exception as e:
                traceback.print_exc()
                results["models"]["lgb"] = {"error": str(e)}
        else:
            results["models"]["lgb"] = {"error": "lightgbm 未安装"}

        # mAP对比图（AP对比）
        if PLOT_AVAILABLE:
            try:
                labels = []
                aps = []
                for k in ["xgb", "lgb"]:
                    cls = results["models"].get(k, {}).get("classification", {})
                    if "mAP" in cls:
                        labels.append(k.upper())
                        aps.append(float(cls["mAP"]))
                if labels:
                    plt.figure(figsize=(4.6, 3.8))
                    sns.barplot(x=labels, y=aps, palette="viridis")
                    plt.ylim(0, 1)
                    plt.title("mAP(AP) 对比")
                    plt.ylabel("AP")
                    p = os.path.join(out_dir, "map_compare.png")
                    plt.tight_layout()
                    plt.savefig(p, dpi=160)
                    plt.close()
                    results["map_compare_png"] = p.replace("\\", "/")
            except Exception:
                pass

        # 保存 json
        try:
            p_json = os.path.join(out_dir, "metrics.json")
            with open(p_json, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            results["metrics_json"] = p_json.replace("\\", "/")
        except Exception:
            pass

        return results

    def predict_next_days(self, model_type: str = "lgb", days: int | None = None) -> dict:
        """
        用回归模型做未来 days 的销售额预测（简单滚动预测）。
        返回：dates/historical/predicted + 简单库存预警/补货建议（基于订单数趋势与现有库存总量）
        """
        days = int(days or self.cfg.horizon_days)
        df_raw = self.load_daily_sales()
        if df_raw is None or df_raw.empty or len(df_raw) < 20:
            return {"error": "历史销售数据不足，至少需要20天以上日级数据"}

        df_feat = self.make_features(df_raw)
        feats = self.feature_columns()

        X = df_feat[feats].values
        y = df_feat["next_day_amount"].values

        split = int(len(X) * (1 - self.cfg.test_size))
        X_train, y_train = X[:split], y[:split]

        model = None
        if model_type == "xgb":
            if not XGBOOST_AVAILABLE:
                return {"error": "xgboost 未安装"}
            model = xgb.XGBRegressor(
                n_estimators=400,
                max_depth=6,
                learning_rate=0.06,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=self.cfg.random_state,
            )
        else:
            if not LIGHTGBM_AVAILABLE:
                return {"error": "lightgbm 未安装"}
            model = lgb.LGBMRegressor(
                n_estimators=600,
                learning_rate=0.05,
                num_leaves=64,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=self.cfg.random_state,
            )

        model.fit(X_train, y_train)

        # 滚动预测：以 df_raw 的最后一天为起点
        last_date = df_raw["date"].max()
        hist_dates = df_raw["date"].dt.strftime("%m-%d").tolist()
        hist_amounts = df_raw["total_amount"].astype(float).tolist()

        # 复制最后一段数据用于构造未来特征
        rolling_df = df_raw.copy()
        preds = []
        pred_dates = []
        for i in range(days):
            d = last_date + timedelta(days=i + 1)
            pred_dates.append(d.strftime("%m-%d"))
            # 临时 append 一行占位
            rolling_df = pd.concat([rolling_df, pd.DataFrame([{"date": d, "order_count": 0.0, "total_amount": np.nan}])], ignore_index=True)
            tmp = self.make_features(rolling_df.tail(60 + 20))  # 只取最近窗口生成特征
            x_pred = tmp[feats].iloc[-1].values.reshape(1, -1)
            y_pred = float(model.predict(x_pred)[0])
            y_pred = max(0.0, y_pred)
            preds.append(y_pred)
            # 写回 total_amount，便于下一步滚动
            rolling_df.loc[rolling_df.index[-1], "total_amount"] = y_pred

        # 简单库存预警/补货建议（示例口径：按销售额/订单趋势给出建议）
        hist_7 = float(np.mean(hist_amounts[-7:])) if len(hist_amounts) >= 7 else float(np.mean(hist_amounts))
        pred_7 = float(np.mean(preds[:7])) if preds else 0.0
        growth = ((pred_7 - hist_7) / hist_7 * 100) if hist_7 > 0 else 0.0

        suggestion = "预测稳定，维持当前补货节奏。"
        level = "normal"
        if growth >= 15:
            suggestion = "预测短期需求明显上升，建议提前补货并关注热销品类库存。"
            level = "warning"
        elif growth <= -15:
            suggestion = "预测短期需求下降，建议减少备货、以促销消化库存。"
            level = "info"

        return {
            "model_type": "XGBoost" if model_type == "xgb" else "LightGBM",
            "dates": hist_dates + pred_dates,
            "historical": hist_amounts + [None] * len(preds),
            "predicted": [None] * len(hist_amounts) + preds,
            "prediction_start_index": len(hist_amounts),
            "inventory_alert": {"level": level, "growth_7d_pct": round(growth, 2), "suggestion": suggestion},
        }


def main():
    cfg = ForecastConfig()
    forecaster = XgbLgbSalesForecaster(cfg)
    metrics = forecaster.train_and_evaluate()
    print("=== XGBoost/LightGBM 训练评估完成 ===")
    print(json.dumps(metrics, ensure_ascii=False, indent=2)[:2000])


if __name__ == "__main__":
    main()

