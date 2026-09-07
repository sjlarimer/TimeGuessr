import csv

CSV_IN  = "Data/Timeguessr_Actuals_Parsed.csv"

# ── 1. Assign subdivision where currently empty ──────────────────────────────
# Keyed by (city, country).  Only applied when the Subdivision cell is blank.
ASSIGN = {
    # Sweden
    ('Stockholm',  'Sweden'): 'Svealand',
    ('Gothenburg', 'Sweden'): 'Gotaland',
    ('Uppsala',    'Sweden'): 'Svealand',
    # Japan
    ('Tokyo',     'Japan'): 'Kanto',
    ('Kobe',      'Japan'): 'Kansai',
    ('Yokohama',  'Japan'): 'Kanto',
    ('Osaka',     'Japan'): 'Kansai',
    ('Nagasaki',  'Japan'): 'Kyushu',
    ('Hiroshima', 'Japan'): 'Chugoku',
    ('Sapporo',   'Japan'): 'Hokkaido',
    ('Yokosuka',  'Japan'): 'Kanto',
    # Greece
    ('Athens',       'Greece'): 'Attica',
    ('Thessaloniki', 'Greece'): 'Central Macedonia',
    ('Poros',        'Greece'): 'Attica',
    ('Kozani',       'Greece'): 'Western Macedonia',
    # Hungary
    ('Budapest',  'Hungary'): 'Central Hungary',
    ('Gyor',      'Hungary'): 'Western Transdanubia',
    ('Gyöngyös',  'Hungary'): 'Northern Hungary',
    # Brazil
    ('Rio de Janeiro', 'Brazil'): 'Southeast',
    ('Sao Paolo',      'Brazil'): 'Southeast',
    ('Sao Paulo',      'Brazil'): 'Southeast',
    ('Brasilia',       'Brazil'): 'Center-West',
    # South Africa
    ('Johannesburg', 'South Africa'): 'Gauteng',
    ('Pretoria',     'South Africa'): 'Gauteng',
    ('Cape Town',    'South Africa'): 'Western Cape',
    ("Gordon's Bay", 'South Africa'): 'Western Cape',
    # Denmark
    ('Copenhagen', 'Denmark'): 'Capital Region',
    # Norway
    ('Oslo',        'Norway'): 'Eastern Norway',
    ('Lillehammer', 'Norway'): 'Eastern Norway',
    ('Tønsberg',    'Norway'): 'Eastern Norway',
    ('Høyanger',    'Norway'): 'Western Norway',
    ('Trondheim',   'Norway'): 'Trondelag',
    # Finland
    ('Helsinki', 'Finland'): 'Helsinki-Uusimaa',
    ('Turku',    'Finland'): 'Southern Finland',
    # Portugal
    ('Lisbon', 'Portugal'): 'Lisbon',
    # Chile
    ('Santiago', 'Chile'): 'Santiago Metropolitan',
    # Israel
    ('Jerusalem', 'Israel'): 'Jerusalem',
    ('Tel Aviv',  'Israel'): 'Tel Aviv',
    # Thailand
    ('Bangkok', 'Thailand'): 'Central Thailand',
    # Vietnam
    ('Ho Chi Minh', 'Vietnam'): 'Southeast',
    ('Hanoi',       'Vietnam'): 'Red River Delta',
    ('Di An',       'Vietnam'): 'Southeast',
    # Turkey
    ('Istanbul', 'Türkiye'): 'Marmara',
    ('Ankara',   'Türkiye'): 'Central Anatolia',
    # Czechia
    ('Prague', 'Czechia'): 'Bohemia',
    ('Brno',   'Czechia'): 'Moravia',
    # Austria
    ('Vienna',                      'Austria'): 'Vienna',
    ('Ramsau am Dachstein',         'Austria'): 'Styria',
    ('St. Anton am Arlberg',        'Austria'): 'Tyrol',
    ('St. Wolfgang im Salzkammergut','Austria'): 'Upper Austria',
    # South Korea
    ('Seoul', 'South Korea'): 'Seoul Capital Area',
    ('Busan', 'South Korea'): 'Gyeongsang',
    # Peru — city "Lima" → province "Lima"; others get their department name
    ('Lima',        'Peru'): 'Lima',
    ('Huepetuhe',   'Peru'): 'Madre de Dios',
    ('Machu Picchu','Peru'): 'Cusco',
    ('Puno',        'Peru'): 'Puno',
    ('Madre de Dios','Peru'): 'Madre de Dios',
    # New Zealand
    ('Wellington',  'New Zealand'): 'Wellington',
    ('Greymouth',   'New Zealand'): 'West Coast',
    ('Invercargill','New Zealand'): 'Southland',
    ('Dunedin',     'New Zealand'): 'Otago',
}

# The very-long NZ town name gets Hawke's Bay
NZ_LONG_NAME_PREFIX = "Taumatawhakatangi"

# ── 2. Rename existing subdivisions (apply regardless of city) ────────────────
# Keyed by (old_subdivision, country) → new_subdivision
RENAME = {
    ('Moscow',            'Russia'): 'Central',
    ('Saint Petersburg',  'Russia'): 'Northwestern',
    ('Community of Madrid','Spain'): 'Madrid',
    ('Valencian Community','Spain'): 'Valencia',
    ('Silesian',          'Poland'): 'Silesia',
    ('Masovian',          'Poland'): 'Masovia',
    ('Pomeranian',        'Poland'): 'Pomerania',
    ('Brussels',         'Belgium'): 'Brussels Capital Region',
    ('Geneva',       'Switzerland'): 'Lake Geneva Region',
    ('Bern',         'Switzerland'): 'Espace Mittelland',
    ('Macao',             'China'): 'Macau',
}

# ── 3. City-specific overrides (wrong geographic assignment in source) ─────────
# Keyed by (city, subdivision, country) → new_subdivision
CITY_SPECIFIC = {
    ('Assisi', 'Lazio', 'Italy'): 'Umbria',
}


def fix_row(city, subdivision, country):
    """Return the corrected subdivision for one CSV row."""
    # City-specific correction first (highest priority)
    city_key = (city, subdivision, country)
    if city_key in CITY_SPECIFIC:
        return CITY_SPECIFIC[city_key]

    # Rename existing non-empty subdivision
    if subdivision:
        rename_key = (subdivision, country)
        if rename_key in RENAME:
            return RENAME[rename_key]
        return subdivision  # already set and no rename needed

    # Assign to empty subdivision
    assign_key = (city, country)
    if assign_key in ASSIGN:
        return ASSIGN[assign_key]

    # Special case: very long NZ town name
    if country == 'New Zealand' and city.startswith(NZ_LONG_NAME_PREFIX):
        return "Hawke's Bay"

    return subdivision  # leave blank if no rule found


def fix_csv():
    rows = []
    with open(CSV_IN, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            city        = row.get('City', '').strip()
            subdivision = row.get('Subdivision', '').strip()
            country     = row.get('Country', '').strip()
            row['Subdivision'] = fix_row(city, subdivision, country)
            rows.append(row)

    with open(CSV_IN, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV updated: {CSV_IN}")


if __name__ == "__main__":
    fix_csv()
