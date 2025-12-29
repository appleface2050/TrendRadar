"""
数据路径统一配置

所有CSV数据文件统一存放在根目录的data文件夹下
此模块提供统一的路径访问接口

项目结构：
/home/shang/git/Indeptrader/
├── data/                          # 根目录数据文件夹（所有CSV文件）
│   ├── raw/                       # 原始数据
│   ├── processed/                 # 处理后数据
│   │   ├── china/                 # 中国数据
│   │   ├── us/                    # 美国数据
│   │   └── global/                # 全球数据
│   └── derived/                   # 衍生数据（模型计算结果）
│       ├── indicators/            # 各类指标
│       ├── yield/                 # 收益率数据
│       └── industry/              # 行业数据
└── MacroTrading/                 # 代码目录（不含CSV文件）
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 数据根目录
DATA_ROOT = PROJECT_ROOT / 'data'

# ============================================
# 处理后数据路径
# ============================================

# 中国市场数据
CHINA_PROCESSED = DATA_ROOT / 'processed/china'
HS300_FILE = DATA_ROOT / 'processed/china/hs300.csv'
M1_M2_FILE = DATA_ROOT / 'processed/china/m1_m2.csv'
BOND_YIELD_10Y_FILE = DATA_ROOT / 'processed/china/bond_yield_10y.csv'
NORTHBOUND_FLOW_FILE = DATA_ROOT / 'processed/china/northbound_flow.csv'

# 行业数据目录
INDUSTRIES_DIR = DATA_ROOT / 'processed/china/industries'

# 美国市场数据
US_PROCESSED = DATA_ROOT / 'processed/us'
SP500_FILE = DATA_ROOT / 'processed/us/sp500.csv'

# 全球数据
GLOBAL_PROCESSED = DATA_ROOT / 'processed/global'
VIX_FILE = DATA_ROOT / 'processed/global/vix.csv'
US_BOND_YIELD_10Y_FILE = DATA_ROOT / 'processed/global/us_bond_yield_10y.csv'
DXY_FILE = DATA_ROOT / 'processed/global/dxy.csv'

# ============================================
# 衍生数据路径
# ============================================

# 指标数据
INDICATORS_DIR = DATA_ROOT / 'derived/indicators'
REGIME_PROBS_FILE = INDICATORS_DIR / 'regime_probabilities.csv'
MACRO_SCORES_FILE = INDICATORS_DIR / 'macro_scores.csv'
RISK_INDEX_FILE = INDICATORS_DIR / 'composite_risk_index.csv'

# 收益率数据
YIELD_DIR = DATA_ROOT / 'derived/yield'

# 行业数据
INDUSTRY_DERIVED_DIR = DATA_ROOT / 'derived/industry'


def get_data_path(relative_path: str) -> Path:
    """
    获取数据文件的完整路径

    Parameters:
    -----------
    relative_path : str
        相对于data目录的路径，例如 'processed/china/hs300.csv'

    Returns:
    --------
    Path
        完整的文件路径
    """
    return DATA_ROOT / relative_path


def ensure_dir(directory: Path) -> Path:
    """
    确保目录存在，不存在则创建

    Parameters:
    -----------
    directory : Path
        目录路径

    Returns:
    --------
    Path
        目录路径
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# 便捷访问函数
def get_hs300() -> Path:
    """获取沪深300数据路径"""
    return HS300_FILE


def get_m1_m2() -> Path:
    """获取M1/M2数据路径"""
    return M1_M2_FILE


def get_bond_yield_10y() -> Path:
    """获取10年期国债收益率路径"""
    return BOND_YIELD_10Y_FILE


def get_northbound_flow() -> Path:
    """获取北向资金流路径"""
    return NORTHBOUND_FLOW_FILE


def get_vix() -> Path:
    """获取VIX数据路径"""
    return VIX_FILE


def get_sp500() -> Path:
    """获取SP500数据路径"""
    return SP500_FILE


def get_industries_dir() -> Path:
    """获取行业数据目录"""
    return INDUSTRIES_DIR


def get_indicators_dir() -> Path:
    """获取指标数据目录"""
    return INDICATORS_DIR


if __name__ == "__main__":
    # 测试路径配置
    print("="*80)
    print("数据路径配置")
    print("="*80)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"数据根目录: {DATA_ROOT}")
    print()
    print("关键数据文件:")
    print(f"  沪深300: {HS300_FILE}")
    print(f"  M1/M2: {M1_M2_FILE}")
    print(f"  10年期国债收益率: {BOND_YIELD_10Y_FILE}")
    print(f"  VIX: {VIX_FILE}")
    print()
    print("目录:")
    print(f"  行业数据: {INDUSTRIES_DIR}")
    print(f"  指标数据: {INDICATORS_DIR}")
    print("="*80)
