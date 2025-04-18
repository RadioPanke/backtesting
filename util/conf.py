import os
from dotenv import load_dotenv
load_dotenv()
# Alpha 5 API requests per minute; 500 API requests per day
# 500 requests/day rate limit lifted
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

FINANCIAL_MODELING_PREP_KEY = os.getenv("FINANCIAL_MODELING_PREP_KEY")

""""WEEKLY"""

removed_outliers_huge_gaps_WEEKLY = [
    'JNK', 'NTES', 'SDS', 'EWU', 'EZU', 'UNG', 'TBT', 'VOO', 'VTI', 'XRT', 'SVXY', 'UPRO', 'FNGD', 'FNGU', 'SRTY',
    'SPXL', 'EWJ', 'GDXJ', 'PSQ', 'XBI', 'IYR', 'SPXS', 'QID', 'SPXU', 'VWO', 'KRE', 'SH', 'SDOW', 'EFA', 'SOXL', 'VXX',
    'IWM', 'IAU', 'TQQQ', 'EEM', 'SLV', 'IJH', 'ILF', 'IJR', 'FXI', 'XRAY', 'XOM', 'VFC', 'UAA', 'TD', 'TAP', 'TCOM',
    'SSO', 'SBUX', 'ROST', 'RIO', 'PHG', 'PGR', 'PENN', 'PEAK', 'OMC', 'OKE', 'NEE', 'MGI', 'LKQ', 'KIM', 'JEF', 'JCI',
    'IGT', 'IBN', 'HBI', 'HAL', 'GIS', 'GILD', 'FAST', 'EW', 'EMR', 'EPD', 'EFA', 'DQ', 'CL', 'CNC', 'C', 'BTI', 'CF',
    'BEN', 'ABT', 'DKS', 'AAPL', 'SGOL', 'VONG'
]

etfs = [
    'ANGL', 'ARKK', 'AAXJ', 'DIA', 'DBC', 'EWC', 'EWG', 'GLD', 'KWEB', 'QQQ', 'SPY', 'USO', 'VGK', 'FLOT', 'SCZ',
    'VNQ', 'VPL', 'VUG', 'XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY',
    'EWZ', 'HYG', 'GDX', 'ITB', 'LQD', 'TLT', 'ARKK', 'IEMG',
    'VEA', 'IEFA', 'PSLV', 'ICLN', 'TNA', 'IEF', 'XOP', 'BKLN', 'EWH', 'GOVT',
    'JETS', 'AGG', 'BND', 'RSX', 'PFF', 'ERX',
    'SJNK', 'EMB', 'ARKG', 'XME', 'SMH', 'INDA', 'IVV', 'XLC', 'SCO',
    'PGX', 'MCHI', 'USMV', 'EWY', 'SPLV', 'VCIT'
]

etfs20 = [
    'VNQ', 'VPL', 'VUG', 'XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY',
    'VEA', 'SPXU', 'ARKK', 'ANGL', 'SCZ'
]

a = ['AA', 'ABBV', 'ADM', 'ALTO', 'AMD']
b = ['BABA', 'BG', 'BKR', 'BK', 'BP']
c = ['CG', 'CLF']
d = ['DHI', 'DISH', 'DXC']
e = ['EIX', 'ES']
f = ['FANG', 'FCX', 'FL']
g = ['GOL', 'GOGL', 'GPS']
h = ['HAS', 'HCA', 'HD']
i = ['IBM', 'INFO', 'INFY']
j = ['JBLU', 'JD', 'JNPR']
k = ['KEY', 'KGC', 'KMB', 'KSS']
l = ['LAC', 'LEVI', 'LLY', 'LMT']
m = ['MAT', 'MDT', 'MET', 'MRK', 'META']
n = ['NIO', 'NTRA', 'NWL']
o = ['O', 'OKTA', 'OMF']
p = ['PFE', 'PRU']
# q = []
r = ['RCL', 'RF', 'RHI']
s = ['SAVE', 'SCHF', 'SE']
t = ['T', 'TDOC']
u = ['UAL', 'UDR', 'UL', 'UNM']
v = ['VIAC', 'VLO', 'VMW', 'VRT']
w = ['WBA', 'WDAY', 'WDC', 'WU']
x = ['X']
# y = []
# z = ['Z']

stocks = a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + r + s + t + u + v + w + x


""""DAILY"""
detfs = [
    'AAXJ', 'DIA', 'EWC', 'EWG', 'FXI', 'GLD', 'IJH', 'IJR', 'ILF', 'KWEB', 'QQQ', 'SLV', 'SPY', 'USO', 'VGK',
    'VNQ', 'VPL', 'VUG', 'XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY', 'EEM', 'TQQQ',
    'EWZ', 'IWM', 'HYG', 'IAU', 'GDX', 'EFA', 'SOXL', 'LQD', 'VXX', 'SDS', 'TLT', 'ARKK', 'IEMG', 'SDOW', 'SH',
    'VWO', 'JNK', 'VEA', 'KRE', 'SPXU', 'IEFA', 'QID', 'PSLV', 'ICLN', 'TNA', 'IEF', 'XOP', 'BKLN', 'EWH', 'GOVT',
    'IYR', 'SPXS', 'XBI', 'GDXJ', 'EWJ', 'PSQ', 'SPXL', 'JETS', 'SRTY', 'AGG', 'BND', 'FNGU', 'RSX', 'PFF', 'ERX',
    'SJNK', 'FNGD', 'EMB', 'ARKG', 'UPRO', 'XME', 'SMH', 'SVXY', 'VTI', 'XRT', 'INDA', 'IVV', 'XLC', 'SCO', 'TBT',
    'VOO', 'PGX', 'UNG', 'MCHI', 'USMV', 'EWY', 'SPLV', 'VCIT', 'EZU', 'EWU', 'ANGL', 'ARKK', 'DBC', 'FLOT', 'ITB',
    'SCZ'
    ]

detfs20 = [
    'VNQ', 'VPL', 'VUG', 'XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY', 'EEM', 'TQQQ',
    'VWO', 'JNK', 'VEA', 'KRE', 'SPXU'
]

a = ['AA', 'ABBV', 'ABT', 'ADM', 'ALTO']
b = ['BABA', 'BEN', 'BG', 'BK', 'BKR', 'BP', 'BTI']
c = ['C', 'CF', 'CG', 'CL', 'CLF', 'CNC']
d = ['DHI', 'DISH', 'DKS', 'DQ', 'DXC']
e = ['EFA', 'EIX', 'EMR', 'EPD', 'ES', 'EW']
f = ['FANG', 'FAST', 'FB', 'FCX', 'FL']
g = ['GIS', 'GOL', 'GILD', 'GOGL', 'GPS']
h = ['HAL', 'HAS', 'HBI', 'HCA', 'HD']
i = ['IBM', 'IBN', 'IGT', 'INFO', 'INFY']
j = ['JBLU', 'JCI', 'JD', 'JEF', 'JNPR']
k = ['KEY', 'KGC', 'KIM', 'KMB', 'KSS']
l = ['LAC', 'LEVI', 'LKQ', 'LLY', 'LMT']
m = ['MAT', 'MDT', 'MET', 'MGI', 'MRK']
n = ['NEE', 'NIO', 'NTES', 'NTRA', 'NWL']
o = ['O', 'OKE', 'OKTA', 'OMC', 'OMF']
p = ['PFE', 'PEAK', 'PENN', 'PGR', 'PHG', 'PRU']
# q = []
r = ['RCL', 'RF', 'RHI', 'RIO', 'ROST']
s = ['SAVE', 'SBUX', 'SCHF', 'SE', 'SSO']
t = ['T', 'TAP', 'TCOM', 'TD', 'TDOC']
u = ['UAA', 'UAL', 'UDR', 'UL', 'UNM']
v = ['VFC', 'VIAC', 'VLO', 'VMW', 'VRT']
w = ['WBA', 'WBT', 'WDAY', 'WDC', 'WU']
x = ['X', 'XOM', 'XRAY']
# y = []
# z = ['Z']