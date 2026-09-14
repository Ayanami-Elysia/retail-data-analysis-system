import os
import requests
import sys
import zipfile
import shutil
import subprocess
import winreg
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 代理配置
PROXIES = {
    'http': 'http://127.0.0.1:7890',  # 常用代理端口
    'https': 'http://127.0.0.1:7890'
}

def set_proxy():
    """设置代理"""
    try:
        # 设置环境变量代理
        os.environ['HTTP_PROXY'] = PROXIES['http']
        os.environ['HTTPS_PROXY'] = PROXIES['https']
        
        # 设置requests代理
        session = requests.Session()
        session.proxies = PROXIES
        return session
    except Exception as e:
        print(f"设置代理时发生错误: {e}")
        return requests.Session()

def check_and_remove_java():
    """检查并删除已安装的Java"""
    try:
        # 检查Java安装
        result = subprocess.run(['java', '-version'], capture_output=True, text=True, stderr=subprocess.STDOUT)
        if 'java version' in result.stdout:
            print("检测到已安装的Java，正在卸载...")
            # 使用wmic卸载Java
            os.system('wmic product where "name like \'Java%%\'" call uninstall /nointeractive')
            print("Java卸载完成")
    except Exception as e:
        print(f"检查Java安装时发生错误: {e}")

def create_session_with_retry():
    """创建带有重试机制的会话"""
    session = set_proxy()  # 使用代理会话
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def download_file(url, filename, timeout=30, max_retries=3):
    """下载文件的通用函数，带有重试机制"""
    session = create_session_with_retry()
    
    for attempt in range(max_retries):
        try:
            print(f"正在下载 {filename}... (尝试 {attempt + 1}/{max_retries})")
            response = session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"{filename} 下载成功！")
                return True
            else:
                print(f"下载失败，HTTP状态码: {response.status_code}")
                
        except Exception as e:
            print(f"下载过程中发生错误: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            continue
            
    return False

def check_manual_java():
    """检查手动安装的Java"""
    try:
        # 检查默认安装目录
        jdk_dir = r"C:\Program Files\Java\jdk1.8.0_202"
        jre_dir = r"C:\Program Files\Java\jre1.8.0_202"
        
        if os.path.exists(jdk_dir) and os.path.isdir(jdk_dir):
            print("检测到JDK安装目录")
            if os.path.exists(jre_dir) and os.path.isdir(jre_dir):
                print("检测到JRE安装目录")
                return jdk_dir
            else:
                print("警告：未检测到JRE目录")
                return jdk_dir
        return None
    except Exception as e:
        print(f"检查手动安装的Java时发生错误: {e}")
        return None

def setup_java_env():
    """设置Java环境"""
    try:
        # 首先检查手动安装的Java
        manual_java_home = check_manual_java()
        if manual_java_home:
            print(f"使用已安装的Java: {manual_java_home}")
            java_home = manual_java_home
        else:
            print("未检测到Java安装，请按以下步骤操作：")
            print("1. 从以下地址下载Java 8：")
            print("   https://repo.huaweicloud.com/java/jdk/8u202-b08/jdk-8u202-windows-x64.exe")
            print("2. 运行安装程序，使用默认安装路径：")
            print("   JDK: C:\\Program Files\\Java\\jdk1.8.0_202")
            print("   JRE: C:\\Program Files\\Java\\jre1.8.0_202")
            print("3. 重新运行此脚本")
            return False
        
        # 设置环境变量
        os.environ['JAVA_HOME'] = java_home
        java_bin = os.path.join(java_home, 'bin')
        os.environ['PATH'] = os.environ['PATH'] + ';' + java_bin
        
        # 设置系统环境变量
        try:
            subprocess.run(['setx', 'JAVA_HOME', java_home], capture_output=True)
            subprocess.run(['setx', 'PATH', f"%PATH%;{java_bin}"], capture_output=True)
            # 添加JRE路径
            jre_bin = os.path.join(r"C:\Program Files\Java\jre1.8.0_202", 'bin')
            if os.path.exists(jre_bin):
                subprocess.run(['setx', 'PATH', f"%PATH%;{jre_bin}"], capture_output=True)
        except Exception as e:
            print(f"设置系统环境变量时发生错误: {e}")
            return False
        
        # 验证Java安装
        try:
            # 修改验证方式
            java_cmd = os.path.join(java_bin, 'java')
            result = subprocess.run([java_cmd, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            version_output = result.stderr if result.stderr else result.stdout  # java -version 通常输出到stderr
            
            if 'java version' in version_output:
                print("Java环境配置成功！")
                print(f"Java版本信息：\n{version_output}")
                return True
            else:
                print("Java环境配置可能有问题，请检查安装")
                print(f"命令输出：\n{version_output}")
                return False
        except Exception as e:
            print(f"验证Java安装时发生错误: {e}")
            print("请确保Java已正确安装，并且安装路径正确")
            return False
            
    except Exception as e:
        print(f"设置Java环境时发生错误: {e}")
        return False

def check_manual_hadoop():
    """检查手动安装的Hadoop"""
    try:
        hadoop_home = r"C:\Program Files\Hadoop"
        hadoop_bin = os.path.join(hadoop_home, "bin")
        
        if os.path.exists(hadoop_home) and os.path.isdir(hadoop_home):
            print("检测到Hadoop安装目录")
            if os.path.exists(hadoop_bin) and os.path.isdir(hadoop_bin):
                print("检测到Hadoop bin目录")
                return hadoop_home
            else:
                print("警告：未检测到bin目录，将创建")
                os.makedirs(hadoop_bin, exist_ok=True)
                return hadoop_home
        return None
    except Exception as e:
        print(f"检查手动安装的Hadoop时发生错误: {e}")
        return None

def setup_hadoop_env():
    """设置Hadoop环境"""
    try:
        # 首先检查手动安装的Hadoop
        manual_hadoop_home = check_manual_hadoop()
        if manual_hadoop_home:
            print(f"使用已安装的Hadoop: {manual_hadoop_home}")
            hadoop_home = manual_hadoop_home
        else:
            print("未检测到Hadoop安装，请按以下步骤操作：")
            print("1. 从以下地址下载Hadoop 3.2.2：")
            print("   https://repo.huaweicloud.com/apache/hadoop/common/hadoop-3.2.2/hadoop-3.2.2.tar.gz")
            print("2. 解压并将内容复制到：C:\\Program Files\\Hadoop")
            print("3. 确保bin目录存在：C:\\Program Files\\Hadoop\\bin")
            print("4. 重新运行此脚本")
            return False

        hadoop_bin = os.path.join(hadoop_home, "bin")
        
        # 检查必要的文件
        required_files = ['winutils.exe', 'hadoop.dll']
        missing_files = []
        for file in required_files:
            if not os.path.exists(os.path.join(hadoop_bin, file)):
                missing_files.append(file)
        
        if missing_files:
            print(f"以下文件缺失: {', '.join(missing_files)}")
            print("尝试下载缺失文件...")
            
            # 多个下载源
            download_sources = {
                "winutils.exe": [
                    "https://github.com/cdarlint/winutils/raw/master/hadoop-3.2.2/bin/winutils.exe",
                    "https://gitee.com/mirrors/winutils/raw/master/hadoop-3.2.2/bin/winutils.exe",
                    "https://raw.githubusercontent.com/kontext-tech/winutils/master/hadoop-3.2.2/bin/winutils.exe",
                    "https://github.com/steveloughran/winutils/raw/master/hadoop-3.2.2/bin/winutils.exe"
                ],
                "hadoop.dll": [
                    "https://github.com/cdarlint/winutils/raw/master/hadoop-3.2.2/bin/hadoop.dll",
                    "https://gitee.com/mirrors/winutils/raw/master/hadoop-3.2.2/bin/hadoop.dll",
                    "https://raw.githubusercontent.com/kontext-tech/winutils/master/hadoop-3.2.2/bin/hadoop.dll",
                    "https://github.com/steveloughran/winutils/raw/master/hadoop-3.2.2/bin/hadoop.dll"
                ]
            }
            
            for file_name in missing_files:
                file_path = os.path.join(hadoop_bin, file_name)
                download_success = False
                
                print(f"\n尝试下载 {file_name}...")
                for url in download_sources[file_name]:
                    print(f"尝试从 {url} 下载...")
                    if download_file(url, file_path):
                        download_success = True
                        break
                    else:
                        print("该源下载失败，尝试下一个源...")
                
                if not download_success:
                    print(f"\n无法下载 {file_name}，请手动下载并放置在 {hadoop_bin} 目录下")
                    print("\n您可以从以下地址手动下载：")
                    print("1. winutils.exe 和 hadoop.dll 的直接下载链接：")
                    for url in download_sources[file_name]:
                        print(f"   {url}")
                    print("\n2. 或者访问以下镜像站手动下载：")
                    print("   - https://github.com/cdarlint/winutils/tree/master/hadoop-3.2.2/bin")
                    print("   - https://gitee.com/mirrors/winutils/tree/master/hadoop-3.2.2/bin")
                    return False

        # 设置环境变量
        os.environ['HADOOP_HOME'] = hadoop_home
        os.environ['PATH'] = os.environ['PATH'] + ';' + hadoop_bin
        
        # 设置系统环境变量
        try:
            subprocess.run(['setx', 'HADOOP_HOME', hadoop_home], capture_output=True)
            subprocess.run(['setx', 'PATH', f"%PATH%;{hadoop_bin}"], capture_output=True)
        except Exception as e:
            print(f"设置系统环境变量时发生错误: {e}")
            return False
        
        print("\nHadoop环境配置成功！")
        print(f"Hadoop安装目录: {hadoop_home}")
        print(f"Hadoop bin目录: {hadoop_bin}")
        return True
        
    except Exception as e:
        print(f"设置Hadoop环境时发生错误: {e}")
        return False

def download_mysql_connector():
    """下载MySQL连接器JAR文件"""
    connector_version = "5.1.49"
    jar_name = f"mysql-connector-java-{connector_version}.jar"
    download_url = f"https://repo1.maven.org/maven2/mysql/mysql-connector-java/{connector_version}/{jar_name}"
    
    try:
        if os.path.exists(jar_name):
            print(f"MySQL连接器已存在: {jar_name}")
            return True
            
        return download_file(download_url, jar_name)
            
    except Exception as e:
        print(f"下载过程中发生错误: {e}")
        return False

def update_spark_config():
    """更新DataCreate.py中的Spark配置"""
    try:
        with open('DataCreate.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新Spark配置
        spark_config = """
# 创建Spark会话
spark = SparkSession.builder \\
    .appName("MCI_Analysis") \\
    .config("spark.jars", "mysql-connector-java-5.1.49.jar") \\
    .config("spark.driver.extraClassPath", "mysql-connector-java-5.1.49.jar") \\
    .config("spark.executor.extraClassPath", "mysql-connector-java-5.1.49.jar") \\
    .config("spark.driver.memory", "4g") \\
    .config("spark.executor.memory", "4g") \\
    .getOrCreate()

# 设置日志级别
spark.sparkContext.setLogLevel("ERROR")
"""
        # 替换原有的Spark配置
        new_content = content.replace(
            '# 创建Spark会话\nspark = SparkSession.builder \\\n    .appName("MCI_Analysis") \\\n    .config("spark.jars", "mysql-connector-java-8.0.27.jar") \\\n    .getOrCreate()',
            spark_config
        )
        
        # 更新MySQL驱动类
        new_content = new_content.replace(
            '"driver": "com.mysql.cj.jdbc.Driver"',
            '"driver": "com.mysql.jdbc.Driver"'
        )
        
        with open('DataCreate.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("Spark配置更新成功！")
        return True
    except Exception as e:
        print(f"更新Spark配置时发生错误: {e}")
        return False

def check_mysql_version():
    """检查MySQL版本"""
    try:
        result = subprocess.run(['mysql', '--version'], capture_output=True, text=True)
        if '5.7.28' not in result.stdout:
            print("警告：当前MySQL版本可能与配置不兼容")
        else:
            print("MySQL版本检查通过")
        return True
    except Exception as e:
        print(f"检查MySQL版本时发生错误: {e}")
        return False

def check_admin():
    """检查管理员权限"""
    try:
        import ctypes
        import sys
        
        if sys.platform == 'win32':
            try:
                # 尝试创建测试文件来验证权限
                test_path = r"C:\Program Files\test.txt"
                with open(test_path, 'w') as f:
                    f.write('test')
                os.remove(test_path)
                return True
            except Exception:
                return False
        return True
    except Exception:
        return False

def main():
    """主函数"""
    try:
        print("开始环境配置...")
        
        # 检查管理员权限
        if not check_admin():
            print("\n警告：此脚本需要管理员权限才能正常运行")
            print("请按以下步骤操作：")
            print("1. 关闭PyCharm")
            print("2. 右键点击PyCharm图标")
            print("3. 选择'以管理员身份运行'")
            print("4. 重新打开项目并运行此脚本")
            return
            
        print("\n1. 检查MySQL版本...")
        check_mysql_version()
        
        print("\n2. 设置Java环境...")
        if not setup_java_env():
            print("Java环境设置失败！")
            return
            
        print("\n3. 安装必要的Python包...")
        os.system(f"{sys.executable} -m pip install --upgrade pip")
        os.system(f"{sys.executable} -m pip install requests findspark pyspark==3.2.2 pandas numpy scikit-learn mlxtend pymysql")
        
        print("\n4. 设置Hadoop环境...")
        if not setup_hadoop_env():
            print("Hadoop环境设置失败！")
            return
        
        print("\n5. 下载MySQL连接器...")
        if not download_mysql_connector():
            print("MySQL连接器下载失败！")
            return
        
        print("\n6. 更新Spark配置...")
        if not update_spark_config():
            print("Spark配置更新失败！")
            return
        
        print("\n所有环境配置完成！")
        print("\n版本信息：")
        print("- Java: 1.8 (Java 8)")
        print("- MySQL: 5.7.28")
        print("- Hadoop: 3.2.2")
        print("- PySpark: 3.2.2")
        print("- MySQL Connector: 5.1.49")
        
        print("\n请重启命令行窗口以使环境变量生效。")
        print("之后您就可以运行DataCreate.py了。")
            
    except Exception as e:
        print(f"设置过程中发生错误: {e}")

if __name__ == "__main__":
    main() 