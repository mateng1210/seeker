import logging
import logging.handlers
from pathlib import Path

# 1. 创建logs目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 2. 定义格式
DETAIL_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
SIMPLE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# 3. 配置Logger
def setup_logging():
    # 根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # 全局最低级别

    # 清除可能已有的处理器，防止重复（Jupyter等环境需要）
    if logger.handlers:
        logger.handlers.clear()

    # ---- 控制台处理器 (开发时看) ----
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 控制台可以看更细
    console_formatter = logging.Formatter(SIMPLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # ---- 文件处理器 (按天轮转，避免单个文件过大) ----
    # 这是关键！用RotatingFileHandler或TimedRotatingFileHandler
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "app.log",
        when="midnight",  # 每天午夜轮转
        interval=1,
        backupCount=30,   # 保留最近30天
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(DETAIL_FORMAT)  # 文件里记详细点
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # ---- 错误日志单独文件 ----
    error_file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)  # 只记录ERROR及以上
    error_file_handler.setFormatter(logging.Formatter(DETAIL_FORMAT))
    logger.addHandler(error_file_handler)

    # 4. 控制第三方库的日志噪音（比如uvicorn访问日志太吵）
    # 官方文档虽然没强调，但根据线上经验，适当调整更清净
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # 如果你用了SQLAlchemy，也可以这样控制SQL日志
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # 最后，记录一条日志表示配置完成
    logger.info("日志系统初始化完成！")

if __name__ == "__main__":
    setup_logging()
