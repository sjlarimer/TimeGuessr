import geopandas as gpd
import pandas as pd
import os
import country_converter as coco

# --- Configuration ---
INPUT_FILE = "./Data/World_Administrative_Divisions.geojson"
OUTPUT_FILE = "./Data/Custom_World_Map.geojson"
SIMPLIFIED_OUTPUT_FILE = "./Data/Custom_World_Map_New.json"

# List of Countries to KEEP subdivisions for (ISO Alpha-3 Codes)
# NOR and FIN stay listed here but only to keep their detached territories
# (Svalbard/Jan Mayen, Peter I Island, Aland) distinct from the mainland — see
# NOR_REGION_MAP / FIN_REGION_MAP below, which collapse every mainland region
# into a single "Norway"/"Finland" entry while leaving those territory rows
# unmapped (and therefore un-dissolved).
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
    'NOR', # Norway (mainland merged; Svalbard/Jan Mayen, Peter I Island kept separate)
    'ESP', # Spain
    'FIN', # Finland (mainland merged; Aland kept separate)
    'IRL', # Ireland
    'RUS', # Russia
    'BRA', # Brazil
    'BEL', # Belgium
    'NZL', # New Zealand
    'IND', # India
    'MEX', # Mexico
    'TUR', # Turkey
    'AUT', # Austria
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

# Every mainland county maps to a single 'NOR' entry so the mainland no longer
# splits into regions — only Svalbard/Jan Mayen and Peter I Island (left
# unmapped, so .fillna() keeps their original names) stay distinct. Named after
# the ISO3 code, not "Norway", so it lines up with the Join_Key a
# subdivision-less Norway round gets in the app's own stats calculation.
NOR_REGION_MAP = {
    'Nordland':             'NOR',
    'Troms og Finnmark':    'NOR',
    'Trøndelag':            'NOR',
    'Vestland':             'NOR',
    'Møre og Romsdal':      'NOR',
    'Rogaland':             'NOR',
    'Sogn og Fjordane':     'NOR',   # old county absorbed into Vestland
    'Oslo':                 'NOR',
    'Viken':                'NOR',
    'Innlandet':            'NOR',
    'Vestfold og Telemark': 'NOR',
    'Agder':                'NOR',
    'Aust-Agder':           'NOR',  # old county absorbed into Agder
}

# Every mainland region maps to a single 'FIN' entry (see NOR_REGION_MAP above
# for why it's the ISO3 code) so the mainland no longer splits into regions —
# only Åland (its own autonomous region) stays distinct.
FIN_REGION_MAP = {
    'Uusimaa':          'FIN',
    'Varsinais-Suomi':  'FIN',
    'Satakunta':        'FIN',
    'Kanta-Häme':       'FIN',
    'Päijät-Häme':      'FIN',
    'Kymenlaakso':      'FIN',
    'Etelä-Karjala':    'FIN',
    'Pirkanmaa':        'FIN',
    'Keski-Suomi':      'FIN',
    'Etelä-Pohjanmaa':  'FIN',
    'Pohjanmaa':        'FIN',
    'Keski-Pohjanmaa':  'FIN',
    'Etelä-Savo':       'FIN',
    'Pohjois-Savo':     'FIN',
    'Pohjois-Karjala':  'FIN',
    'Kainuu':           'FIN',
    'Pohjois-Pohjanmaa':'FIN',
    'Lappi':            'FIN',
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

    print("SPLITTING: Carving Kosovo out of Serbia as its own country...")
    if 'NAME' in gdf.columns:
        kos_mask = gdf['NAME'] == 'Kosovo-Metohija'
        if kos_mask.any():
            gdf.loc[kos_mask, 'ISO3'] = 'XKX'
            gdf.loc[kos_mask, 'NAME'] = 'Kosovo'
        else:
            print("   - ⚠️ 'Kosovo-Metohija' row not found in source data; skipping split.")

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

    print("MERGING: Merging Indian Daman/Dadra duplicate and translating names...")
    if 'NAME' in gdf_final.columns:
        ind_mask = gdf_final['ISO3'] == 'IND'
        gdf_ind = gdf_final[ind_mask].copy()
        gdf_rest = gdf_final[~ind_mask].copy()
        gdf_ind['NAME'] = gdf_ind['NAME'].map(IND_NAME_MAP).fillna(gdf_ind['NAME'])
        gdf_ind = gdf_ind.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_ind], ignore_index=True)

    print("MERGING: Dissolving Russian subdivisions into 8 federal districts...")
    if 'NAME' in gdf_final.columns:
        rus_mask = gdf_final['ISO3'] == 'RUS'
        gdf_rus = gdf_final[rus_mask].copy()
        gdf_rest = gdf_final[~rus_mask].copy()
        gdf_rus['NAME'] = gdf_rus['NAME'].map(RUS_REGION_MAP).fillna(gdf_rus['NAME'])
        gdf_rus = gdf_rus.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_rus], ignore_index=True)

    print("MERGING: Dissolving Norwegian mainland counties into one shape (Svalbard/Jan Mayen, Peter I Island stay separate)...")
    if 'NAME' in gdf_final.columns:
        nor_mask = gdf_final['ISO3'] == 'NOR'
        gdf_nor = gdf_final[nor_mask].copy()
        gdf_rest = gdf_final[~nor_mask].copy()
        gdf_nor['NAME'] = gdf_nor['NAME'].map(NOR_REGION_MAP).fillna(gdf_nor['NAME'])
        gdf_nor = gdf_nor.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_nor], ignore_index=True)

    print("MERGING: Dissolving Finnish mainland regions into one shape (Aland stays separate)...")
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

    print("MERGING: Dissolving Turkish provinces into 7 geographical regions...")
    if 'NAME' in gdf_final.columns:
        tur_mask = gdf_final['ISO3'] == 'TUR'
        gdf_tur = gdf_final[tur_mask].copy()
        gdf_rest = gdf_final[~tur_mask].copy()
        gdf_tur['NAME'] = gdf_tur['NAME'].map(TUR_REGION_MAP).fillna(gdf_tur['NAME'])
        gdf_tur = gdf_tur.dissolve(by='NAME', as_index=False)
        gdf_final = pd.concat([gdf_rest, gdf_tur], ignore_index=True)

    print("RENAMING: Translating Austrian state names to English...")
    if 'NAME' in gdf_final.columns:
        aut_mask = gdf_final['ISO3'] == 'AUT'
        gdf_final.loc[aut_mask, 'NAME'] = gdf_final.loc[aut_mask, 'NAME'].replace(AUT_NAME_MAP)

    print("RENAMING: Cleaning up Mexican state names...")
    if 'NAME' in gdf_final.columns:
        mex_mask = gdf_final['ISO3'] == 'MEX'
        gdf_final.loc[mex_mask, 'NAME'] = gdf_final.loc[mex_mask, 'NAME'].replace(MEX_NAME_MAP)

    print("RENAMING: Cleaning up New Zealand region names...")
    if 'NAME' in gdf_final.columns:
        nzl_mask = gdf_final['ISO3'] == 'NZL'
        gdf_final.loc[nzl_mask, 'NAME'] = gdf_final.loc[nzl_mask, 'NAME'].replace(NZL_NAME_MAP)

    print("RENAMING: Translating Belgian region names to English...")
    if 'NAME' in gdf_final.columns:
        bel_mask = gdf_final['ISO3'] == 'BEL'
        gdf_final.loc[bel_mask, 'NAME'] = gdf_final.loc[bel_mask, 'NAME'].replace(BEL_NAME_MAP)

    print("RENAMING: Naming the merged Danish mainland shape 'DNK'...")
    # DNK is no longer in COUNTRIES_TO_KEEP_SPLIT, so its regions were already
    # dissolved into one row above; Greenland and the Faroe Islands are separate
    # ISO3 entities (GRL/FRO) untouched by this and stay distinct on their own.
    # Named after the ISO3 code (not "Denmark") so it lines up with the Join_Key
    # a subdivision-less Denmark round gets in the app's own stats calculation —
    # a plain ISO3 code, resolved to a nice display name at the labeling stage,
    # same as every other split country's own played-but-unassigned rounds.
    if 'NAME' in gdf_final.columns:
        dnk_mask = gdf_final['ISO3'] == 'DNK'
        gdf_final.loc[dnk_mask, 'NAME'] = 'DNK'

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
