import geopandas as gpd
import pandas as pd
import os
import country_converter as coco

# --- Configuration ---
INPUT_FILE = "./Data/World_Administrative_Divisions.geojson"
OUTPUT_FILE = "./Data/Custom_World_Map.geojson"
SIMPLIFIED_OUTPUT_FILE = "./Data/Custom_World_Map_New.json"

# List of Countries to KEEP subdivisions for (ISO Alpha-3 Codes)
COUNTRIES_TO_KEEP_SPLIT = [
    'USA', # United States
    'GBR', # United Kingdom
    'FRA', # France
    'NLD', # Netherlands
    'ITA', # Italy
    'CAN', # Canada
    'DEU', # Germany
    'POL', # Poland
    'SWE', # Sweden
    'JPN', # Japan
    'AUS', # Australia
    'CHN', # China
    'CHE', # Switzerland
    'HUN', # Hungary
    'GRC', # Greece
    'DNK', # Denmark
    'NOR', # Norway
    'ESP', # Spain
    'FIN', # Finland
    'IRL', # Ireland
    'RUS', # Russia
    'BRA', # Brazil
    'BEL', # Belgium
    'KOR', # South Korea
    'PRT', # Portugal
    'NZL', # New Zealand
    'IND', # India
    'ZAF', # South Africa
    'MEX', # Mexico
    'PER', # Peru
    'TUR', # Turkey
    'AUT', # Austria
    'VNM', # Vietnam
    'CZE', # Czechia
    'THA', # Thailand
    'CHL', # Chile
    'ISR', # Israel
]

FRA_NAME_MAP = {
    'Bretagne':                   'Brittany',
    'Bourgogne-Franche-Comté':    'Burgundy-Franche-Comte',
    'Corse':                      'Corsica',
    'Normandie':                  'Normandy',
    'Nouvelle-Aquitaine':         'New Aquitaine',
    'Occitanie':                  'Occitania',
    'Île-de-France':              'Ile-de-France',
    'Auvergne-Rhône-Alpes':       'Auvergne-Rhone-Alpes',
    "Provence-Alpes-Côte d'Azur": "Provence-Alpes-Cote d'Azur",
    'Réunion':                    'Reunion',
}

CHN_NAME_MAP = {
    # Provinces — strip "Sheng"
    'Anhui Sheng':        'Anhui',
    'Fujian Sheng':       'Fujian',
    'Gansu Sheng':        'Gansu',
    'Guangdong Sheng':    'Guangdong',
    'Guizhou Sheng':      'Guizhou',
    'Hainan Sheng':       'Hainan',
    'Hebei Sheng':        'Hebei',
    'Heilongjiang Sheng': 'Heilongjiang',
    'Henan Sheng':        'Henan',
    'Hubei Sheng':        'Hubei',
    'Hunan Sheng':        'Hunan',
    'Jiangsu Sheng':      'Jiangsu',
    'Jiangxi Sheng':      'Jiangxi',
    'Jilin Sheng':        'Jilin',
    'Liaoning Sheng':     'Liaoning',
    'Qinghai Sheng':      'Qinghai',
    'Shaanxi Sheng':      'Shaanxi',
    'Shandong Sheng':     'Shandong',
    'Shanxi Sheng':       'Shanxi',
    'Sichuan Sheng':      'Sichuan',
    'Yunnan Sheng':       'Yunnan',
    'Zhejiang Sheng':     'Zhejiang',
    # Municipalities — strip "Shi"
    'Beijing Shi':   'Beijing',
    'Chongqing Shi': 'Chongqing',
    'Shanghai Shi':  'Shanghai',
    'Tianjin Shi':   'Tianjin',
    # Autonomous Regions — translate to English
    'Guangxi Zhuangzu Zizhiqu': 'Guangxi',
    'Nei Mongol Zizhiqu':       'Inner Mongolia',
    'Ningxia Zizhiiqu':         'Ningxia',
    'Xinjiang Uygur Zizhiqu':   'Xinjiang',
    'Xizang Zizhiqu':           'Tibet',
    # Special Administrative Regions
    'Macao': 'Macau',
}

NLD_NAME_MAP = {
    'Fryslân':    'Friesland',
    'Noord-Brabant': 'North Brabant',
    'Noord-Holland': 'North Holland',
    'Zuid-Holland':  'South Holland',
}

ITA_NAME_MAP = {
    'Lombardia': 'Lombardy',
    'Piemonte':  'Piedmont',
    'Sardegna':  'Sardinia',
    'Sicilia':   'Sicily',
    'Toscana':   'Tuscany',
}

DEU_NAME_MAP = {
    'Bayern':                  'Bavaria',
    'Hessen':                  'Hesse',
    'Mecklenburg-Vorpommern':  'Mecklenburg-Western Pomerania',
    'Niedersachsen':           'Lower Saxony',
    'Nordrhein-Westfalen':     'North Rhine-Westphalia',
    'Rheinland-Pfalz':         'Rhineland-Palatinate',
    'Sachsen':                 'Saxony',
    'Sachsen-Anhalt':          'Saxony-Anhalt',
    'Thüringen':               'Thuringia',
    'Baden-Württemberg':       'Baden-Wurttemberg',
}

SWE_REGION_MAP = {
    # Norrland
    'Norrbottens län':     'Norrland',
    'Västerbottens län':   'Norrland',
    'Västernorrlands län': 'Norrland',
    'Jämtlands län':       'Norrland',
    'Gävleborgs län':      'Norrland',
    # Svealand
    'Dalarnas län':        'Svealand',
    'Stockholms län':      'Svealand',
    'Uppsala län':         'Svealand',
    'Södermanlands län':   'Svealand',
    'Värmlands län':       'Svealand',
    'Västmanlands län':    'Svealand',
    'Örebro län':          'Svealand',
    # Götaland
    'Östergötlands län':   'Gotaland',
    'Jönköpings län':      'Gotaland',
    'Kronobergs län':      'Gotaland',
    'Kalmar län':          'Gotaland',
    'Gotlands län':        'Gotaland',
    'Blekinge län':        'Gotaland',
    'Skåne län':           'Gotaland',
    'Hallands län':        'Gotaland',
    'Västra Götalands län':'Gotaland',
}

JPN_REGION_MAP = {
    # Hokkaido
    'Hokkaidô':  'Hokkaido',
    # Tohoku
    'Aomori':    'Tohoku',
    'Iwate':     'Tohoku',
    'Miyagi':    'Tohoku',
    'Akita':     'Tohoku',
    'Yamagata':  'Tohoku',
    'Hukusima':  'Tohoku',
    # Kanto
    'Ibaraki':   'Kanto',
    'Totigi':    'Kanto',
    'Gunma':     'Kanto',
    'Saitama':   'Kanto',
    'Tiba':      'Kanto',
    'Tôkyô':     'Kanto',
    'Kanagawa':  'Kanto',
    # Chubu
    'Niigata':   'Chubu',
    'Toyama':    'Chubu',
    'Isikawa':   'Chubu',
    'Hukui':     'Chubu',
    'Yamanasi':  'Chubu',
    'Nagano':    'Chubu',
    'Gihu':      'Chubu',
    'Sizuoka':   'Chubu',
    'Aiti':      'Chubu',
    # Kansai
    'Mie':       'Kansai',
    'Siga':      'Kansai',
    'Kyôto':     'Kansai',
    'Ôsaka':     'Kansai',
    'Hyôgo':     'Kansai',
    'Nara':      'Kansai',
    'Wakayama':  'Kansai',
    # Chugoku
    'Tottori':   'Chugoku',
    'Simane':    'Chugoku',
    'Okayama':   'Chugoku',
    'Hirosima':  'Chugoku',
    'Yamaguti':  'Chugoku',
    # Shikoku
    'Tokusima':  'Shikoku',
    'Kagawa':    'Shikoku',
    'Ehime':     'Shikoku',
    'Kôti':      'Shikoku',
    # Kyushu
    'Hukuoka':   'Kyushu',
    'Saga':      'Kyushu',
    'Nagasaki':  'Kyushu',
    'Kumamoto':  'Kyushu',
    'Ôita':      'Kyushu',
    'Miyazaki':  'Kyushu',
    'Kagosima':  'Kyushu',
    # Okinawa
    'Okinawa':   'Okinawa',
}

DNK_NAME_MAP = {
    'Hovedstaden': 'Capital Region',
    'Midtjylland': 'Central Jutland',
    'Nordjylland': 'North Jutland',
    'Sjælland':    'Zealand',
    'Syddanmark':  'Southern Denmark',
}

GRC_REGION_MAP = {
    'Ágion Óros':                    'Mount Athos',
    'Aitoloakarnanía':               'Western Greece',
    'Anatolikí Makedonía kai Thráki':'Eastern Macedonia and Thrace',
    'Attikí':                        'Attica',
    'Dytikí Makedonía':              'Western Macedonia',
    'Ileía':                         'Western Greece',
    'Ionía Nísia':                   'Ionian Islands',
    'Ípeiros':                       'Epirus',
    'Kentrikí Makedonía':            'Central Macedonia',
    'Kríti':                         'Crete',
    'Nótio Aigaío':                  'South Aegean',
    'Pelopónnisos':                  'Peloponnese',
    'Stereá Elláda':                 'Central Greece',
    'Thessalía':                     'Thessaly',
    'Vóreio Aigaío':                 'North Aegean',
}

HUN_REGION_MAP = {
    # Central Hungary
    'Budapest': 'Central Hungary',
    'Pest':     'Central Hungary',
    # Central Transdanubia
    'Fejér':              'Central Transdanubia',
    'Komárom-Esztergom':  'Central Transdanubia',
    'Veszprém':           'Central Transdanubia',
    # Western Transdanubia
    'Gyór-Moson-Sopron': 'Western Transdanubia',
    'Vas':               'Western Transdanubia',
    'Zala':              'Western Transdanubia',
    # Southern Transdanubia
    'Baranya': 'Southern Transdanubia',
    'Somogy':  'Southern Transdanubia',
    'Tolna':   'Southern Transdanubia',
    # Northern Hungary
    'Borsod-Abaúj-Zemplén': 'Northern Hungary',
    'Heves':                 'Northern Hungary',
    'Nógrád':                'Northern Hungary',
    # Northern Great Plain
    'Hajdú-Bihar':            'Northern Great Plain',
    'Jász-Nagykun-Szolnok':   'Northern Great Plain',
    'Szabolcs-Szatmár-Bereg': 'Northern Great Plain',
    # Southern Great Plain
    'Bács-Kiskun': 'Southern Great Plain',
    'Békés':       'Southern Great Plain',
    'Csongrád':    'Southern Great Plain',
}

CHE_REGION_MAP = {
    # Lake Geneva Region
    'Genève':   'Lake Geneva Region',
    'Vaud':     'Lake Geneva Region',
    'Wallis':   'Lake Geneva Region',
    # Espace Mittelland
    'Bern':      'Espace Mittelland',
    'Freiburg':  'Espace Mittelland',
    'Solothurn': 'Espace Mittelland',
    'Neuchâtel': 'Espace Mittelland',
    'Jura':      'Espace Mittelland',
    # Northwestern Switzerland
    'Basel-Stadt':      'Northwestern Switzerland',
    'Basel-Landschaft': 'Northwestern Switzerland',
    'Aargau':           'Northwestern Switzerland',
    # Zürich
    'Zürich': 'Zurich',
    # Eastern Switzerland
    'Glarus':                  'Eastern Switzerland',
    'Schaffhausen':            'Eastern Switzerland',
    'Appenzell Ausserrhoden':  'Eastern Switzerland',
    'Appenzell Innerrhoden':   'Eastern Switzerland',
    'Sankt Gallen':            'Eastern Switzerland',
    'Graubünden':              'Eastern Switzerland',
    'Thurgau':                 'Eastern Switzerland',
    # Central Switzerland
    'Luzern':    'Central Switzerland',
    'Uri':       'Central Switzerland',
    'Schwyz':    'Central Switzerland',
    'Obwalden':  'Central Switzerland',
    'Nidwalden': 'Central Switzerland',
    'Zug':       'Central Switzerland',
    # Ticino
    'Ticino': 'Ticino',
}

PRT_REGION_MAP = {
    # Norte
    'Braga':            'Norte',
    'Bragança':         'Norte',
    'Porto':            'Norte',
    'Viana do Castelo': 'Norte',
    'Vila Real':        'Norte',
    # Centro
    'Aveiro':          'Centro',
    'Castelo Branco':  'Centro',
    'Coimbra':         'Centro',
    'Guarda':          'Centro',
    'Leiria':          'Centro',
    'Santarém':        'Centro',
    'Viseu':           'Centro',
    # Lisbon Metropolitan Area
    'Lisboa':  'Lisbon',
    'Setúbal': 'Lisbon',
    # Alentejo
    'Beja':       'Alentejo',
    'Évora':      'Alentejo',
    'Portalegre': 'Alentejo',
    # Algarve
    'Faro': 'Algarve',
    # Autonomous Regions
    'Região Autónoma dos Açores': 'Azores',
    'Região Autónoma da Madeira': 'Madeira',
}

THA_REGION_MAP = {
    # Northern Thailand
    'Chiang Mai':  'Northern Thailand',
    'Chiang Rai':  'Northern Thailand',
    'Lampang':     'Northern Thailand',
    'Lamphun':     'Northern Thailand',
    'Mae Hong Son':'Northern Thailand',
    'Nan':         'Northern Thailand',
    'Phayao':      'Northern Thailand',
    'Phrae':       'Northern Thailand',
    'Uttaradit':   'Northern Thailand',
    # Northeastern Thailand (Isan)
    'Amnat Charoen':    'Northeastern Thailand',
    'Bueng Kan':        'Northeastern Thailand',
    'Buri Ram':         'Northeastern Thailand',
    'Chaiyaphum':       'Northeastern Thailand',
    'Kalasin':          'Northeastern Thailand',
    'Khon Kaen':        'Northeastern Thailand',
    'Loei':             'Northeastern Thailand',
    'Maha Sarakham':    'Northeastern Thailand',
    'Mukdahan':         'Northeastern Thailand',
    'Nakhon Phanom':    'Northeastern Thailand',
    'Nakhon Ratchasima':'Northeastern Thailand',
    'Nong Bua Lam Phu': 'Northeastern Thailand',
    'Nong Khai':        'Northeastern Thailand',
    'Roi Et':           'Northeastern Thailand',
    'Sakon Nakhon':     'Northeastern Thailand',
    'Si sa ket':        'Northeastern Thailand',
    'Surin':            'Northeastern Thailand',
    'Ubon Ratchathani': 'Northeastern Thailand',
    'Udon Thani':       'Northeastern Thailand',
    'Yasothon':         'Northeastern Thailand',
    # Central Thailand
    'Ang Thong':             'Central Thailand',
    'Chai Nat':              'Central Thailand',
    'Kamphaeng Phet':        'Central Thailand',
    'Krung Thep Maha Nakhon':'Central Thailand',
    'Lop Buri':              'Central Thailand',
    'Nakhon Nayok':          'Central Thailand',
    'Nakhon Pathom':         'Central Thailand',
    'Nakhon Sawan':          'Central Thailand',
    'Nonthaburi':            'Central Thailand',
    'Pathum Thani':          'Central Thailand',
    'Phatthaya':             'Central Thailand',
    'Phetchabun':            'Central Thailand',
    'Phichit':               'Central Thailand',
    'Phitsanulok':           'Central Thailand',
    'Phra Nakhon Si Ayutthaya':'Central Thailand',
    'Samut Prakan':          'Central Thailand',
    'Samut Sakhon':          'Central Thailand',
    'Samut Songkhram':       'Central Thailand',
    'Saraburi':              'Central Thailand',
    'Sing Buri':             'Central Thailand',
    'Sukhothai':             'Central Thailand',
    'Suphan Buri':           'Central Thailand',
    'Uthai Thani':           'Central Thailand',
    # Eastern Thailand
    'Chachoengsao': 'Eastern Thailand',
    'Chanthaburi':  'Eastern Thailand',
    'Chon Buri':    'Eastern Thailand',
    'Prachin Buri': 'Eastern Thailand',
    'Rayong':       'Eastern Thailand',
    'Sa Kaeo':      'Eastern Thailand',
    'Trat':         'Eastern Thailand',
    # Western Thailand
    'Kanchanaburi':      'Western Thailand',
    'Phetchaburi':       'Western Thailand',
    'Prachuap Khiri Khan':'Western Thailand',
    'Ratchaburi':        'Western Thailand',
    'Tak':               'Western Thailand',
    # Southern Thailand
    'Chumphon':          'Southern Thailand',
    'Krabi':             'Southern Thailand',
    'Nakhon Si Thammarat':'Southern Thailand',
    'Narathiwat':        'Southern Thailand',
    'Pattani':           'Southern Thailand',
    'Phangnga':          'Southern Thailand',
    'Phatthalung':       'Southern Thailand',
    'Phuket':            'Southern Thailand',
    'Ranong':            'Southern Thailand',
    'Satun':             'Southern Thailand',
    'Songkhla':          'Southern Thailand',
    'Surat Thani':       'Southern Thailand',
    'Trang':             'Southern Thailand',
    'Yala':              'Southern Thailand',
}

CHL_NAME_MAP = {
    'Aisén del General Carlos Ibañez del Campo': 'Aysen',
    'Biobío':                                    'Biobio',
    'La Araucanía':                              'Araucania',
    "Libertador General Bernardo O'Higgins":     "O'Higgins",
    'Los Ríos':                                  'Los Rios',
    'Región Metropolitana de Santiago':          'Santiago Metropolitan',
    'Tarapacá':                                  'Tarapaca',
    'Valparaíso':                                'Valparaiso',
    'Ñuble':                                     'Nuble',
}

ISR_NAME_MAP = {
    'HaDarom':           'Southern District',
    'HaMerkaz':          'Central District',
    'HaTsafon':          'Northern District',
    'H̱efa':        'Haifa',
    'Tel-Aviv':          'Tel Aviv',
    'Yerushalayim':      'Jerusalem',
}

AUT_NAME_MAP = {
    'Kärnten':          'Carinthia',
    'Niederösterreich': 'Lower Austria',
    'Oberösterreich':   'Upper Austria',
    'Steiermark':       'Styria',
    'Tirol':            'Tyrol',
    'Wien':             'Vienna',
}

TUR_REGION_MAP = {
    # Marmara
    'İstanbul':   'Marmara',
    'Tekirdağ':   'Marmara',
    'Edirne':     'Marmara',
    'Kırklareli': 'Marmara',
    'Balıkesir':  'Marmara',
    'Çanakkale':  'Marmara',
    'Bursa':      'Marmara',
    'Kocaeli':    'Marmara',
    'Sakarya':    'Marmara',
    'Yalova':     'Marmara',
    'Bilecik':    'Marmara',
    'Düzce':      'Marmara',
    'Bolu':       'Marmara',
    # Aegean
    'İzmir':          'Aegean',
    'Manisa':         'Aegean',
    'Afyonkarahisar': 'Aegean',
    'Kütahya':        'Aegean',
    'Aydin':          'Aegean',
    'Denizli':        'Aegean',
    'Muğla':          'Aegean',
    'Uşak':           'Aegean',
    # Mediterranean
    'Antalya':        'Mediterranean',
    'Isparta':        'Mediterranean',
    'Burdur':         'Mediterranean',
    'Adana':          'Mediterranean',
    'Mersin':         'Mediterranean',
    'Hatay':          'Mediterranean',
    'Kahramanmaraş':  'Mediterranean',
    'Osmaniye':       'Mediterranean',
    # Central Anatolia
    'Ankara':    'Central Anatolia',
    'Konya':     'Central Anatolia',
    'Eskişehir': 'Central Anatolia',
    'Karaman':   'Central Anatolia',
    'Aksaray':   'Central Anatolia',
    'Nevşehir':  'Central Anatolia',
    'Kırıkkale': 'Central Anatolia',
    'Kırşehir':  'Central Anatolia',
    'Niğde':     'Central Anatolia',
    'Yozgat':    'Central Anatolia',
    'Sivas':     'Central Anatolia',
    'Kayseri':   'Central Anatolia',
    'Çankırı':   'Central Anatolia',
    # Black Sea
    'Zonguldak':  'Black Sea',
    'Bartın':     'Black Sea',
    'Karabük':    'Black Sea',
    'Kastamonu':  'Black Sea',
    'Sinop':      'Black Sea',
    'Samsun':     'Black Sea',
    'Ordu':       'Black Sea',
    'Giresun':    'Black Sea',
    'Trabzon':    'Black Sea',
    'Rize':       'Black Sea',
    'Artvin':     'Black Sea',
    'Gümüşhane':  'Black Sea',
    'Bayburt':    'Black Sea',
    'Tokat':      'Black Sea',
    'Amasya':     'Black Sea',
    'Çorum':      'Black Sea',
    # Eastern Anatolia
    'Erzurum':  'Eastern Anatolia',
    'Erzincan': 'Eastern Anatolia',
    'Ağrı':     'Eastern Anatolia',
    'Kars':     'Eastern Anatolia',
    'Iğdır':    'Eastern Anatolia',
    'Ardahan':  'Eastern Anatolia',
    'Malatya':  'Eastern Anatolia',
    'Elazığ':   'Eastern Anatolia',
    'Bingöl':   'Eastern Anatolia',
    'Tunceli':  'Eastern Anatolia',
    'Van':      'Eastern Anatolia',
    'Muş':      'Eastern Anatolia',
    'Bitlis':   'Eastern Anatolia',
    'Hakkâri':  'Eastern Anatolia',
    # Southeastern Anatolia
    'Gaziantep':  'Southeastern Anatolia',
    'Kilis':      'Southeastern Anatolia',
    'Şanlıurfa':  'Southeastern Anatolia',
    'Diyarbakır': 'Southeastern Anatolia',
    'Mardin':     'Southeastern Anatolia',
    'Batman':     'Southeastern Anatolia',
    'Şırnak':     'Southeastern Anatolia',
    'Siirt':      'Southeastern Anatolia',
    'Adıyaman':   'Southeastern Anatolia',
}

VNM_REGION_MAP = {
    # Northwest
    'Lai Châu':   'Northwest',
    'Điện Biên':  'Northwest',
    'Sơn La':     'Northwest',
    'Hòa Bình':   'Northwest',
    # Northeast
    'Hà Giang':   'Northeast',
    'Cao Bằng':   'Northeast',
    'Bắc Kạn':    'Northeast',
    'Lạng Sơn':   'Northeast',
    'Tuyên Quang':'Northeast',
    'Lào Cai':    'Northeast',
    'Yên Bái':    'Northeast',
    'Thái Nguyên':'Northeast',
    'Phú Thọ':    'Northeast',
    'Bắc Giang':  'Northeast',
    'Quảng Ninh': 'Northeast',
    # Red River Delta
    'Hà Nội':    'Red River Delta',
    'Vĩnh Phúc': 'Red River Delta',
    'Bắc Ninh':  'Red River Delta',
    'Hà Nam':    'Red River Delta',
    'Hưng Yên':  'Red River Delta',
    'Hải Dương': 'Red River Delta',
    'Hải Phòng': 'Red River Delta',
    'Thái Bình': 'Red River Delta',
    'Nam Ðịnh':  'Red River Delta',
    'Ninh Bình': 'Red River Delta',
    # North Central Coast
    'Thanh Hóa':      'North Central Coast',
    'Nghệ An':        'North Central Coast',
    'Hà Tĩnh':        'North Central Coast',
    'Quảng Bình':     'North Central Coast',
    'Quảng Trị':      'North Central Coast',
    'Thừa Thiên-Huế': 'North Central Coast',
    # South Central Coast
    'Đà Nẵng':   'South Central Coast',
    'Quảng Nam': 'South Central Coast',
    'Quảng Ngãi':'South Central Coast',
    'Bình Định': 'South Central Coast',
    'Phú Yên':   'South Central Coast',
    'Khánh Hòa': 'South Central Coast',
    'Ninh Thuận':'South Central Coast',
    'Bình Thuận':'South Central Coast',
    # Central Highlands
    'Kon Tum':  'Central Highlands',
    'Gia Lai':  'Central Highlands',
    'Đắk Lắk': 'Central Highlands',
    'Đắk Nông': 'Central Highlands',
    'Lâm Ðồng': 'Central Highlands',
    # Southeast
    'Hồ Chí Minh':       'Southeast',
    'Bình Phước':        'Southeast',
    'Tây Ninh':          'Southeast',
    'Bình Dương':        'Southeast',
    'Ðồng Nai':          'Southeast',
    'Bà Rịa - Vũng Tàu':'Southeast',
    # Mekong River Delta
    'Long An':    'Mekong River Delta',
    'Tiền Giang': 'Mekong River Delta',
    'Bến Tre':    'Mekong River Delta',
    'Ðồng Tháp': 'Mekong River Delta',
    'An Giang':   'Mekong River Delta',
    'Vĩnh Long':  'Mekong River Delta',
    'Trà Vinh':   'Mekong River Delta',
    'Hậu Giang':  'Mekong River Delta',
    'Kiến Giang': 'Mekong River Delta',
    'Sóc Trăng':  'Mekong River Delta',
    'Bạc Liêu':   'Mekong River Delta',
    'Cà Mau':     'Mekong River Delta',
    'Cần Thơ':    'Mekong River Delta',
}

CZE_REGION_MAP = {
    # Bohemia
    'Praha, Hlavní město': 'Bohemia',
    'Středočeský kraj':    'Bohemia',
    'Jihočeský kraj':      'Bohemia',
    'Plzeňský kraj':       'Bohemia',
    'Karlovarský kraj':    'Bohemia',
    'Ústecký kraj':        'Bohemia',
    'Liberecký kraj':      'Bohemia',
    'Královéhradecký kraj':'Bohemia',
    'Pardubický kraj':     'Bohemia',
    'Vysočina':            'Bohemia',
    # Moravia
    'Jihomoravský kraj':   'Moravia',
    'Olomoucký kraj':      'Moravia',
    'Zlínský kraj':        'Moravia',
    # Silesia
    'Moravskoslezský kraj':'Silesia',
}

MEX_NAME_MAP = {
    'Ciudad de México':             'Mexico City',
    'Coahuila de Zaragoza':         'Coahuila',
    'México':                       'Mexico State',
    'Michoacán de Ocampo':          'Michoacan',
    'Nuevo León':                   'Nuevo Leon',
    'Querétaro':                    'Queretaro',
    'San Luis Potosí':              'San Luis Potosi',
    'Veracruz de Ignacio de la Llave': 'Veracruz',
    'Yucatán':                      'Yucatan',
}

PER_NAME_MAP = {
    'Apurímac':                        'Apurimac',
    'El Callao':                       'Callao',
    'Huánuco':                         'Huanuco',
    'Junín':                           'Junin',
    'Lima':                            'Lima Region',
    'Municipalidad Metropolitana de Lima': 'Lima',
    'San Martín':                      'San Martin',
}

NZL_NAME_MAP = {
    'Gisborne District':        'Gisborne',
    'Marlborough District':     'Marlborough',
    'Nelson City':              'Nelson',
    'Tasman District':          'Tasman',
    'Chatham Islands Territory':'Chatham Islands',
}

IND_NAME_MAP = {
    # Diacritics stripped
    "Arunāchal Pradesh":  'Arunachal Pradesh',
    'Bihār':              'Bihar',
    'Chhattīsgarh':       'Chhattisgarh',
    'Gujarāt':            'Gujarat',
    'Haryāna':            'Haryana',
    'Himāchal Pradesh':   'Himachal Pradesh',
    'Jammu and Kashmīr':  'Jammu and Kashmir',
    'Jhārkhand':          'Jharkhand',
    'Karnātaka':          'Karnataka',
    'Ladākh':             'Ladakh',
    'Mahārāshtra':        'Maharashtra',
    'Meghālaya':          'Meghalaya',
    'Nāgāland':           'Nagaland',
    'Rājasthān':          'Rajasthan',
    'Tamil Nādu':         'Tamil Nadu',
    'Telangāna':          'Telangana',
    'Uttarākhand':        'Uttarakhand',
    # Merge old Daman and Diu (DD) into the 2020-unified territory (DH)
    'Dādra and Nagar Haveli and Damān and Diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'Daman and Diu':                            'Dadra and Nagar Haveli and Daman and Diu',
}

BEL_NAME_MAP = {
    'Bruxelles-Capitale: Région de': 'Brussels Capital Region',
    'Vlaamse Gewest':                'Flanders',
    'wallonne, Région':              'Wallonia',
}

KOR_REGION_MAP = {
    # Seoul Capital Area
    'Seoul-teukbyeolsi':   'Seoul Capital Area',
    'Incheon-gwangyeoksi': 'Seoul Capital Area',
    'Gyeonggi-do':         'Seoul Capital Area',
    # Gangwon
    'Gangwon-do':          'Gangwon',
    # Chungcheong
    'Chungcheongbuk-do':   'Chungcheong',
    'Chungcheongnam-do':   'Chungcheong',
    'Daejeon-gwangyeoksi': 'Chungcheong',
    'Sejong':              'Chungcheong',
    # Jeolla
    'Jeollabuk-do':        'Jeolla',
    'Jeollanam-do':        'Jeolla',
    'Gwangju-gwangyeoksi': 'Jeolla',
    # Gyeongsang
    'Gyeongsangbuk-do':    'Gyeongsang',
    'Gyeongsangnam-do':    'Gyeongsang',
    'Daegu-gwangyeoksi':   'Gyeongsang',
    'Busan-gwangyeoksi':   'Gyeongsang',
    'Ulsan-gwangyeoksi':   'Gyeongsang',
    # Jeju
    'Jeju-teukbyeoljachido': 'Jeju',
}

BRA_REGION_MAP = {
    # North
    'Acre':      'North',
    'Amapá':     'North',
    'Amazonas':  'North',
    'Pará':      'North',
    'Rondônia':  'North',
    'Roraima':   'North',
    'Tocantins': 'North',
    # Northeast
    'Alagoas':             'Northeast',
    'Bahia':               'Northeast',
    'Ceará':               'Northeast',
    'Maranhão':            'Northeast',
    'Paraíba':             'Northeast',
    'Pernambuco':          'Northeast',
    'Piauí':               'Northeast',
    'Rio Grande do Norte': 'Northeast',
    'Sergipe':             'Northeast',
    # Center-West
    'Distrito Federal':  'Center-West',
    'Goiás':             'Center-West',
    'Mato Grosso':       'Center-West',
    'Mato Grosso do Sul':'Center-West',
    # Southeast
    'Espírito Santo': 'Southeast',
    'Minas Gerais':   'Southeast',
    'Rio de Janeiro': 'Southeast',
    'São Paulo':      'Southeast',
    # South
    'Paraná':          'South',
    'Rio Grande do Sul':'South',
    'Santa Catarina':   'South',
}

RUS_REGION_MAP = {
    # Central Federal District
    'Belgorodskaya oblast\'':   'Central',
    'Bryanskaya oblast\'':      'Central',
    'Ivanovskaya oblast\'':     'Central',
    'Kaluzhskaya oblast\'':     'Central',
    'Kostromskaya oblast\'':    'Central',
    'Kurskaya oblast\'':        'Central',
    'Lipetskaya oblast\'':      'Central',
    'Moskovskaya oblast\'':     'Central',
    'Moskva':                   'Central',
    'Orlovskaya oblast\'':      'Central',
    'Ryazanskaya oblast\'':     'Central',
    'Smolenskaya oblast\'':     'Central',
    'Tambovskaya oblast\'':     'Central',
    'Tverskaya oblast\'':       'Central',
    "Tul'skaya oblast'":        'Central',
    'Vladimirskaya oblast\'':   'Central',
    'Voronezhskaya oblast\'':   'Central',
    'Yaroslavskaya oblast\'':   'Central',
    # Northwestern Federal District
    "Arkhangel'skaya oblast'":  'Northwestern',
    'Vologodskaya oblast\'':    'Northwestern',
    'Kaliningradskaya oblast\'':'Northwestern',
    'Kareliya, Respublika':     'Northwestern',
    'Komi, Respublika':         'Northwestern',
    'Leningradskaya oblast\'':  'Northwestern',
    'Murmanskaya oblast\'':     'Northwestern',
    'Nenetskiy avtonomnyy okrug': 'Northwestern',
    'Novgorodskaya oblast\'':   'Northwestern',
    'Pskovskaya oblast\'':      'Northwestern',
    'Sankt-Peterburg':          'Northwestern',
    # Southern Federal District
    'Adygeya, Respublika':      'Southern',
    'Astrakhanskaya oblast\'':  'Southern',
    'Kalmykiya, Respublika':    'Southern',
    'Krasnodyarskiy kray':      'Southern',
    'Rostovskaya oblast\'':     'Southern',
    'Volgogradskaya oblast\'':  'Southern',
    # North Caucasian Federal District
    'Chechenskaya Respublika':              'North Caucasian',
    'Dagestan, Respublika':                 'North Caucasian',
    'Ingushskaya, Respublika':              'North Caucasian',
    'Kabardino-Balkarskaya Respublika':     'North Caucasian',
    'Karachayevo-Cherkesskaya Respublika':  'North Caucasian',
    'Severnaya Osetiya-Alaniya, Respublika':'North Caucasian',
    "Stavropol'skiy kray":                  'North Caucasian',
    # Volga Federal District
    'Bashkortostan, Respublika': 'Volga',
    'Chuvashskaya Respublika':   'Volga',
    'Kirovskaya oblast\'':       'Volga',
    'Mariy El, Respublika':      'Volga',
    'Mordoviya, Respublika':     'Volga',
    'Nizhegorodskaya oblast\'':  'Volga',
    'Orenburgskaya oblast\'':    'Volga',
    'Penzenskaya oblast\'':      'Volga',
    'Permskiy kray':             'Volga',
    'Samarskaya oblast\'':       'Volga',
    'Saratovskaya oblast\'':     'Volga',
    'Tatarstan, Respublika':     'Volga',
    'Udmurtskaya Respublika':    'Volga',
    "Ul'yanovskaya oblast'":     'Volga',
    # Ural Federal District
    'Chelyabinskaya oblast\'':          'Ural',
    'Khanty-Mansiyskiy avtonomnyy okrug':'Ural',
    'Kurganskaya oblast\'':             'Ural',
    'Sverdlovskaya oblast\'':           'Ural',
    'Tyumenskaya oblast\'':             'Ural',
    'Yamalo-Nenentskiy avtonomnyy okrug':'Ural',
    # Siberian Federal District
    'Altay, Respublika':        'Siberian',
    'Altayskiy kray':           'Siberian',
    'Irkutskaya oblast\'':      'Siberian',
    'Kemerovskaya oblast\'':    'Siberian',
    'Khakasiya, Respublika':    'Siberian',
    'Krasnoyarskiy kray':       'Siberian',
    'Novosibirskaya oblast\'':  'Siberian',
    'Omskaya oblast\'':         'Siberian',
    'Tomskaya oblast\'':        'Siberian',
    'Tyva, Respublika':         'Siberian',
    # Far Eastern Federal District (post-2018 boundaries)
    "Amurskaya oblast'":        'Far Eastern',
    'Buryatiya, Respublika':    'Far Eastern',
    'Chukotskiy avtonomnyy okrug': 'Far Eastern',
    'Khabarovskiy kray':        'Far Eastern',
    'Kamchatskiy kray':         'Far Eastern',
    'Magadanskaya oblast\'':    'Far Eastern',
    'Primorskiy kray':          'Far Eastern',
    'Sakha, Respublika':        'Far Eastern',
    'Sakhalinskaya oblast\'':   'Far Eastern',
    "Yeveryskaya avtonomnaya oblast'": 'Far Eastern',
    "Zabaykal'skiy kray":       'Far Eastern',
}

NOR_REGION_MAP = {
    # Northern Norway
    'Nordland':             'Northern Norway',
    'Troms og Finnmark':    'Northern Norway',
    # Trøndelag (both old ISO_SUB codes)
    'Trøndelag':            'Trondelag',
    # Western Norway
    'Vestland':             'Western Norway',
    'Møre og Romsdal':      'Western Norway',
    'Rogaland':             'Western Norway',
    'Sogn og Fjordane':     'Western Norway',   # old county absorbed into Vestland
    # Eastern Norway
    'Oslo':                 'Eastern Norway',
    'Viken':                'Eastern Norway',
    'Innlandet':            'Eastern Norway',
    'Vestfold og Telemark': 'Eastern Norway',
    # Southern Norway
    'Agder':                'Southern Norway',
    'Aust-Agder':           'Southern Norway',  # old county absorbed into Agder
}

FIN_REGION_MAP = {
    # Helsinki-Uusimaa
    'Uusimaa':          'Helsinki-Uusimaa',
    # Southern Finland
    'Varsinais-Suomi':  'Southern Finland',
    'Satakunta':        'Southern Finland',
    'Kanta-Häme':       'Southern Finland',
    'Päijät-Häme':      'Southern Finland',
    'Kymenlaakso':      'Southern Finland',
    'Etelä-Karjala':    'Southern Finland',
    # Western Finland
    'Pirkanmaa':        'Western Finland',
    'Keski-Suomi':      'Western Finland',
    'Etelä-Pohjanmaa':  'Western Finland',
    'Pohjanmaa':        'Western Finland',
    'Keski-Pohjanmaa':  'Western Finland',
    # Eastern Finland
    'Etelä-Savo':       'Eastern Finland',
    'Pohjois-Savo':     'Eastern Finland',
    'Pohjois-Karjala':  'Eastern Finland',
    'Kainuu':           'Eastern Finland',
    # Northern Finland
    'Pohjois-Pohjanmaa':'Northern Finland',
    'Lappi':            'Northern Finland',
    # Åland stays as its own autonomous region
    'Ahvenanmaan maakunta': 'Aland',
}

ESP_REGION_MAP = {
    # Autonomous Communities — translations and simplifications
    'Andalucía':                   'Andalusia',
    'Aragón':                      'Aragon',
    'Asturias, Principado de':     'Asturias',
    'Canarias':                    'Canary Islands',
    'Castilla y León':             'Castile and Leon',
    'Castilla-La Mancha':          'Castile-La Mancha',
    'Catalunya':                   'Catalonia',
    'Illes Balears':               'Balearic Islands',
    'Madrid, Comunidad de':        'Madrid',
    'Murcia, Región de':           'Murcia',
    'Navarra, Comunidad Foral de': 'Navarre',
    'País Vasco':                  'Basque Country',
    'Valenciana, Comunidad':       'Valencia',
    # Minor North African territories — merge into nearest city
    'Peñón de Vélez de la Gomera': 'Ceuta',
    'Peñón de Alhucemas':          'Ceuta',
    'Isla del Rey':                'Ceuta',
    'Isla Congreso':               'Melilla',
    'Isla de Mar':                 'Melilla',
    'Isla de Tierra':              'Melilla',
    'Isla Isabel II':              'Melilla',
}

POL_NAME_MAP = {
    'Dolnośląskie':       'Lower Silesia',
    'Kujawsko-pomorskie': 'Kuyavian-Pomeranian',
    'Łódzkie':            'Lodz',
    'Lubelskie':          'Lublin',
    'Lubuskie':           'Lubusz',
    'Małopolskie':        'Lesser Poland',
    'Mazowieckie':        'Masovia',
    'Opolskie':           'Opole',
    'Podkarpackie':       'Subcarpathian',
    'Podlaskie':          'Podlachia',
    'Pomorskie':          'Pomerania',
    'Śląskie':            'Silesia',
    'Świętokrzyskie':     'Holy Cross',
    'Warmińsko-mazurskie':'Warmia-Masuria',
    'Wielkopolskie':      'Greater Poland',
    'Zachodniopomorskie': 'West Pomerania',
}

def process_map():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file not found at {INPUT_FILE}")
        return

    print(f"READING: {INPUT_FILE}...")
    try:
        gdf = gpd.read_file(INPUT_FILE)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    print(f"✅ Loaded {len(gdf)} rows.")

    if 'ISO3' not in gdf.columns:
        print("PROCESSING: Generating standard ISO3 codes...")
        source_col = 'ISO_CC' if 'ISO_CC' in gdf.columns else 'COUNTRY'
        if source_col not in gdf.columns:
            print(f"❌ Error: Could not find 'ISO_CC' or 'COUNTRY' to generate ISO3 codes.")
            print(f"Columns found: {list(gdf.columns)}")
            return
        names = gdf[source_col].fillna('Unknown').tolist()
        gdf['ISO3'] = coco.convert(names=names, to='ISO3', not_found=None)

    country_col = 'ISO3'
    print("✅ ISO3 column ready.")

    print(f"PROCESSING: Keeping subdivisions for {COUNTRIES_TO_KEEP_SPLIT}...")
    gdf_split = gdf[gdf[country_col].isin(COUNTRIES_TO_KEEP_SPLIT)].copy()
    gdf_dissolve_source = gdf[~gdf[country_col].isin(COUNTRIES_TO_KEEP_SPLIT)].copy()

    print(f"   - Rows to keep split: {len(gdf_split)}")
    print(f"   - Rows to dissolve:   {len(gdf_dissolve_source)}")

    if not gdf_dissolve_source.empty:
        print("DISSOLVING: Merging borders for the rest of the world...")
        gdf_dissolved = gdf_dissolve_source.dissolve(by=country_col, as_index=False)
    else:
        gdf_dissolved = gpd.GeoDataFrame()

    print("COMBINING: merging layers...")
    gdf_final = pd.concat([gdf_split, gdf_dissolved], ignore_index=True)

    print("MERGING: Dissolving Portuguese districts into 7 NUTS-2 regions...")
    if 'NAME' in gdf_final.columns:
        prt_mask = gdf_final['ISO3'] == 'PRT'
        gdf_prt = gdf_final[prt_mask].copy()
        gdf_rest = gdf_final[~prt_mask].copy()
        gdf_prt['NAME'] = gdf_prt['NAME'].map(PRT_REGION_MAP).fillna(gdf_prt['NAME'])
        gdf_prt = gdf_prt.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_prt], ignore_index=True)

    print("MERGING: Merging Indian Daman/Dadra duplicate and translating names...")
    if 'NAME' in gdf_final.columns:
        ind_mask = gdf_final['ISO3'] == 'IND'
        gdf_ind = gdf_final[ind_mask].copy()
        gdf_rest = gdf_final[~ind_mask].copy()
        gdf_ind['NAME'] = gdf_ind['NAME'].map(IND_NAME_MAP).fillna(gdf_ind['NAME'])
        gdf_ind = gdf_ind.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_ind], ignore_index=True)

    print("MERGING: Dissolving South Korean subdivisions into 6 traditional regions...")
    if 'NAME' in gdf_final.columns:
        kor_mask = gdf_final['ISO3'] == 'KOR'
        gdf_kor = gdf_final[kor_mask].copy()
        gdf_rest = gdf_final[~kor_mask].copy()
        gdf_kor['NAME'] = gdf_kor['NAME'].map(KOR_REGION_MAP).fillna(gdf_kor['NAME'])
        gdf_kor = gdf_kor.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_kor], ignore_index=True)

    print("MERGING: Dissolving Brazilian states into 5 macroregions...")
    if 'NAME' in gdf_final.columns:
        bra_mask = gdf_final['ISO3'] == 'BRA'
        gdf_bra = gdf_final[bra_mask].copy()
        gdf_rest = gdf_final[~bra_mask].copy()
        gdf_bra['NAME'] = gdf_bra['NAME'].map(BRA_REGION_MAP).fillna(gdf_bra['NAME'])
        gdf_bra = gdf_bra.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_bra], ignore_index=True)

    print("MERGING: Dissolving Russian subdivisions into 8 federal districts...")
    if 'NAME' in gdf_final.columns:
        rus_mask = gdf_final['ISO3'] == 'RUS'
        gdf_rus = gdf_final[rus_mask].copy()
        gdf_rest = gdf_final[~rus_mask].copy()
        gdf_rus['NAME'] = gdf_rus['NAME'].map(RUS_REGION_MAP).fillna(gdf_rus['NAME'])
        gdf_rus = gdf_rus.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_rus], ignore_index=True)

    print("MERGING: Dissolving Norwegian counties into 5 traditional regions...")
    if 'NAME' in gdf_final.columns:
        nor_mask = gdf_final['ISO3'] == 'NOR'
        gdf_nor = gdf_final[nor_mask].copy()
        gdf_rest = gdf_final[~nor_mask].copy()
        gdf_nor['NAME'] = gdf_nor['NAME'].map(NOR_REGION_MAP).fillna(gdf_nor['NAME'])
        gdf_nor = gdf_nor.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_nor], ignore_index=True)

    print("MERGING: Dissolving Finnish regions into 5 NUTS-2 regions...")
    if 'NAME' in gdf_final.columns:
        fin_mask = gdf_final['ISO3'] == 'FIN'
        gdf_fin = gdf_final[fin_mask].copy()
        gdf_rest = gdf_final[~fin_mask].copy()
        gdf_fin['NAME'] = gdf_fin['NAME'].map(FIN_REGION_MAP).fillna(gdf_fin['NAME'])
        gdf_fin = gdf_fin.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_fin], ignore_index=True)

    print("MERGING: Dissolving Spanish regions and North African territories...")
    if 'NAME' in gdf_final.columns:
        esp_mask = gdf_final['ISO3'] == 'ESP'
        gdf_esp = gdf_final[esp_mask].copy()
        gdf_rest = gdf_final[~esp_mask].copy()
        gdf_esp['NAME'] = gdf_esp['NAME'].map(ESP_REGION_MAP).fillna(gdf_esp['NAME'])
        gdf_esp = gdf_esp.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_esp], ignore_index=True)

    print("MERGING: Dissolving Greek regions into English-named regions...")
    if 'NAME' in gdf_final.columns:
        grc_mask = gdf_final['ISO3'] == 'GRC'
        gdf_grc = gdf_final[grc_mask].copy()
        gdf_rest = gdf_final[~grc_mask].copy()
        gdf_grc['NAME'] = gdf_grc['NAME'].map(GRC_REGION_MAP).fillna(gdf_grc['NAME'])
        gdf_grc = gdf_grc.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_grc], ignore_index=True)

    print("MERGING: Dissolving Hungarian counties into 7 regions...")
    if 'NAME' in gdf_final.columns:
        hun_mask = gdf_final['ISO3'] == 'HUN'
        gdf_hun = gdf_final[hun_mask].copy()
        gdf_rest = gdf_final[~hun_mask].copy()
        gdf_hun['NAME'] = gdf_hun['NAME'].map(HUN_REGION_MAP).fillna(gdf_hun['NAME'])
        gdf_hun = gdf_hun.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_hun], ignore_index=True)

    print("MERGING: Dissolving Swiss cantons into 7 regions...")
    if 'NAME' in gdf_final.columns:
        che_mask = gdf_final['ISO3'] == 'CHE'
        gdf_che = gdf_final[che_mask].copy()
        gdf_rest = gdf_final[~che_mask].copy()
        gdf_che['NAME'] = gdf_che['NAME'].map(CHE_REGION_MAP).fillna(gdf_che['NAME'])
        gdf_che = gdf_che.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_che], ignore_index=True)

    print("MERGING: Dissolving Japanese prefectures into regions...")
    if 'NAME' in gdf_final.columns:
        jpn_mask = gdf_final['ISO3'] == 'JPN'
        gdf_jpn = gdf_final[jpn_mask].copy()
        gdf_rest = gdf_final[~jpn_mask].copy()
        gdf_jpn['NAME'] = gdf_jpn['NAME'].map(JPN_REGION_MAP).fillna(gdf_jpn['NAME'])
        gdf_jpn = gdf_jpn.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_jpn], ignore_index=True)

    print("MERGING: Dissolving Swedish counties into Norrland, Svealand, Götaland...")
    if 'NAME' in gdf_final.columns:
        swe_mask = gdf_final['ISO3'] == 'SWE'
        gdf_swe = gdf_final[swe_mask].copy()
        gdf_rest = gdf_final[~swe_mask].copy()
        gdf_swe['NAME'] = gdf_swe['NAME'].map(SWE_REGION_MAP).fillna(gdf_swe['NAME'])
        gdf_swe = gdf_swe.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_swe], ignore_index=True)

    print("RENAMING: Cleaning up Chinese subdivision names...")
    if 'NAME' in gdf_final.columns:
        chn_mask = gdf_final['ISO3'] == 'CHN'
        gdf_final.loc[chn_mask, 'NAME'] = gdf_final.loc[chn_mask, 'NAME'].replace(CHN_NAME_MAP)

    print("RENAMING: Translating French region names to English...")
    if 'NAME' in gdf_final.columns:
        fra_mask = gdf_final['ISO3'] == 'FRA'
        gdf_final.loc[fra_mask, 'NAME'] = gdf_final.loc[fra_mask, 'NAME'].replace(FRA_NAME_MAP)

    print("MERGING: Dissolving Canadian province/territory duplicates...")
    if 'NAME' in gdf_final.columns:
        can_mask = gdf_final['ISO3'] == 'CAN'
        gdf_can = gdf_final[can_mask].copy()
        gdf_rest = gdf_final[~can_mask].copy()
        gdf_can = gdf_can.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_can], ignore_index=True)

    print("MERGING: Dissolving Thai provinces into 6 geographical regions...")
    if 'NAME' in gdf_final.columns:
        tha_mask = gdf_final['ISO3'] == 'THA'
        gdf_tha = gdf_final[tha_mask].copy()
        gdf_rest = gdf_final[~tha_mask].copy()
        gdf_tha['NAME'] = gdf_tha['NAME'].map(THA_REGION_MAP).fillna(gdf_tha['NAME'])
        gdf_tha = gdf_tha.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_tha], ignore_index=True)

    print("MERGING: Dissolving Turkish provinces into 7 geographical regions...")
    if 'NAME' in gdf_final.columns:
        tur_mask = gdf_final['ISO3'] == 'TUR'
        gdf_tur = gdf_final[tur_mask].copy()
        gdf_rest = gdf_final[~tur_mask].copy()
        gdf_tur['NAME'] = gdf_tur['NAME'].map(TUR_REGION_MAP).fillna(gdf_tur['NAME'])
        gdf_tur = gdf_tur.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_tur], ignore_index=True)

    print("MERGING: Dissolving Vietnamese provinces into 8 official regions...")
    if 'NAME' in gdf_final.columns:
        vnm_mask = gdf_final['ISO3'] == 'VNM'
        gdf_vnm = gdf_final[vnm_mask].copy()
        gdf_rest = gdf_final[~vnm_mask].copy()
        gdf_vnm['NAME'] = gdf_vnm['NAME'].map(VNM_REGION_MAP).fillna(gdf_vnm['NAME'])
        gdf_vnm = gdf_vnm.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_vnm], ignore_index=True)

    print("MERGING: Dissolving Czech regions into 3 traditional lands...")
    if 'NAME' in gdf_final.columns:
        cze_mask = gdf_final['ISO3'] == 'CZE'
        gdf_cze = gdf_final[cze_mask].copy()
        gdf_rest = gdf_final[~cze_mask].copy()
        gdf_cze['NAME'] = gdf_cze['NAME'].map(CZE_REGION_MAP).fillna(gdf_cze['NAME'])
        gdf_cze = gdf_cze.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_cze], ignore_index=True)

    print("RENAMING: Cleaning up Chilean region names...")
    if 'NAME' in gdf_final.columns:
        chl_mask = gdf_final['ISO3'] == 'CHL'
        gdf_final.loc[chl_mask, 'NAME'] = gdf_final.loc[chl_mask, 'NAME'].replace(CHL_NAME_MAP)

    print("RENAMING: Translating Israeli district names to English...")
    if 'NAME' in gdf_final.columns:
        isr_mask = gdf_final['ISO3'] == 'ISR'
        gdf_final.loc[isr_mask, 'NAME'] = gdf_final.loc[isr_mask, 'NAME'].replace(ISR_NAME_MAP)

    print("RENAMING: Translating Austrian state names to English...")
    if 'NAME' in gdf_final.columns:
        aut_mask = gdf_final['ISO3'] == 'AUT'
        gdf_final.loc[aut_mask, 'NAME'] = gdf_final.loc[aut_mask, 'NAME'].replace(AUT_NAME_MAP)

    print("RENAMING: Cleaning up Mexican state names...")
    if 'NAME' in gdf_final.columns:
        mex_mask = gdf_final['ISO3'] == 'MEX'
        gdf_final.loc[mex_mask, 'NAME'] = gdf_final.loc[mex_mask, 'NAME'].replace(MEX_NAME_MAP)

    print("RENAMING: Cleaning up Peruvian region names...")
    if 'NAME' in gdf_final.columns:
        per_mask = gdf_final['ISO3'] == 'PER'
        gdf_final.loc[per_mask, 'NAME'] = gdf_final.loc[per_mask, 'NAME'].replace(PER_NAME_MAP)

    print("RENAMING: Cleaning up New Zealand region names...")
    if 'NAME' in gdf_final.columns:
        nzl_mask = gdf_final['ISO3'] == 'NZL'
        gdf_final.loc[nzl_mask, 'NAME'] = gdf_final.loc[nzl_mask, 'NAME'].replace(NZL_NAME_MAP)

    print("RENAMING: Translating Belgian region names to English...")
    if 'NAME' in gdf_final.columns:
        bel_mask = gdf_final['ISO3'] == 'BEL'
        gdf_final.loc[bel_mask, 'NAME'] = gdf_final.loc[bel_mask, 'NAME'].replace(BEL_NAME_MAP)

    print("RENAMING: Translating Danish region names to English...")
    if 'NAME' in gdf_final.columns:
        dnk_mask = gdf_final['ISO3'] == 'DNK'
        gdf_final.loc[dnk_mask, 'NAME'] = gdf_final.loc[dnk_mask, 'NAME'].replace(DNK_NAME_MAP)

    print("RENAMING: Translating Dutch province names to English...")
    if 'NAME' in gdf_final.columns:
        nld_mask = gdf_final['ISO3'] == 'NLD'
        gdf_final.loc[nld_mask, 'NAME'] = gdf_final.loc[nld_mask, 'NAME'].replace(NLD_NAME_MAP)

    print("RENAMING: Translating Italian region names to English...")
    if 'NAME' in gdf_final.columns:
        ita_mask = gdf_final['ISO3'] == 'ITA'
        gdf_final.loc[ita_mask, 'NAME'] = gdf_final.loc[ita_mask, 'NAME'].replace(ITA_NAME_MAP)

    print("RENAMING: Translating German state names to English...")
    if 'NAME' in gdf_final.columns:
        deu_mask = gdf_final['ISO3'] == 'DEU'
        gdf_final.loc[deu_mask, 'NAME'] = gdf_final.loc[deu_mask, 'NAME'].replace(DEU_NAME_MAP)

    print("RENAMING: Translating Polish voivodeship names to English...")
    if 'NAME' in gdf_final.columns:
        pol_mask = gdf_final['ISO3'] == 'POL'
        gdf_final.loc[pol_mask, 'NAME'] = gdf_final.loc[pol_mask, 'NAME'].replace(POL_NAME_MAP)

    print("RENAMING: Normalizing non-ASCII country name columns...")
    COUNTRY_NAME_MAP = {
        "Côte d'Ivoire":           "Cote d'Ivoire",
        'Réunion':                  'Reunion',
        'São Tomé and Príncipe':    'Sao Tome and Principe',
    }
    for col in ['COUNTRY', 'COUNTRYAFF']:
        if col in gdf_final.columns:
            gdf_final[col] = gdf_final[col].replace(COUNTRY_NAME_MAP)

    print(f"WRITING: Saving to {OUTPUT_FILE}...")
    try:
        gdf_final.to_file(OUTPUT_FILE, driver='GeoJSON')
        print("✅ GeoJSON saved.")
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return

    print(f"SIMPLIFYING: Applying mapshaper Visvalingam 1.5% (keep-shapes, topological)...")
    import subprocess, shutil
    mapshaper_cmd = shutil.which("mapshaper") or "mapshaper"
    result = subprocess.run(
        [mapshaper_cmd, OUTPUT_FILE,
         "-simplify", "1.5%", "visvalingam", "keep-shapes",
         "-o", SIMPLIFIED_OUTPUT_FILE, "format=geojson"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ Done! Simplified file saved to {SIMPLIFIED_OUTPUT_FILE}")
    else:
        print(f"❌ mapshaper error: {result.stderr or result.stdout}")

if __name__ == "__main__":
    process_map()
