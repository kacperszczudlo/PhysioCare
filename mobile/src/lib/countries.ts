/**
 * @file countries.ts
 * @description Słownik państw oraz prefiksów telefonicznych ze wsparciem dla wyszukiwania i formatowania opcji kierunkowych.
 */

/**
 * Struktura danych o kraju i jego kodzie telefonicznym.
 */
export interface CountryDial {
  /** Kod ISO 3166-1 alpha-2 kraju (np. 'PL') */
  code: string
  /** Polskojęzyczna nazwa kraju */
  name: string
  /** Cyfry kodu kierunkowego bez znaku + (np. '48') */
  dial: string
}

/** Domyślny kod kraju stosowany w aplikacji (Polska) */
export const DEFAULT_COUNTRY_CODE = 'PL'

/** Lista państw wraz z polskimi nazwami i prefiksami kierunkowymi */
export const COUNTRIES: CountryDial[] = [
  { code: 'AF', name: 'Afganistan', dial: '93' },
  { code: 'AL', name: 'Albania', dial: '355' },
  { code: 'DZ', name: 'Algieria', dial: '213' },
  { code: 'AD', name: 'Andora', dial: '376' },
  { code: 'AO', name: 'Angola', dial: '244' },
  { code: 'AI', name: 'Anguilla', dial: '1264' },
  { code: 'AG', name: 'Antigua i Barbuda', dial: '1268' },
  { code: 'AR', name: 'Argentyna', dial: '54' },
  { code: 'AM', name: 'Armenia', dial: '374' },
  { code: 'AW', name: 'Aruba', dial: '297' },
  { code: 'AU', name: 'Australia', dial: '61' },
  { code: 'AT', name: 'Austria', dial: '43' },
  { code: 'AZ', name: 'Azerbejdżan', dial: '994' },
  { code: 'BS', name: 'Bahamy', dial: '1242' },
  { code: 'BH', name: 'Bahrajn', dial: '973' },
  { code: 'BD', name: 'Bangladesz', dial: '880' },
  { code: 'BB', name: 'Barbados', dial: '1246' },
  { code: 'BE', name: 'Belgia', dial: '32' },
  { code: 'BZ', name: 'Belize', dial: '501' },
  { code: 'BJ', name: 'Benin', dial: '229' },
  { code: 'BM', name: 'Bermudy', dial: '1441' },
  { code: 'BT', name: 'Bhutan', dial: '975' },
  { code: 'BY', name: 'Białoruś', dial: '375' },
  { code: 'BO', name: 'Boliwia', dial: '591' },
  { code: 'BW', name: 'Botswana', dial: '267' },
  { code: 'BA', name: 'Bośnia i Hercegowina', dial: '387' },
  { code: 'BR', name: 'Brazylia', dial: '55' },
  { code: 'BN', name: 'Brunei', dial: '673' },
  { code: 'BF', name: 'Burkina Faso', dial: '226' },
  { code: 'BI', name: 'Burundi', dial: '257' },
  { code: 'BG', name: 'Bułgaria', dial: '359' },
  { code: 'CL', name: 'Chile', dial: '56' },
  { code: 'CN', name: 'Chiny', dial: '86' },
  { code: 'HR', name: 'Chorwacja', dial: '385' },
  { code: 'CW', name: 'Curaçao', dial: '599' },
  { code: 'CY', name: 'Cypr', dial: '357' },
  { code: 'TD', name: 'Czad', dial: '235' },
  { code: 'ME', name: 'Czarnogóra', dial: '382' },
  { code: 'CZ', name: 'Czechy', dial: '420' },
  { code: 'DK', name: 'Dania', dial: '45' },
  { code: 'CD', name: 'Demokratyczna Republika Konga', dial: '243' },
  { code: 'DM', name: 'Dominika', dial: '1767' },
  { code: 'DO', name: 'Dominikana', dial: '1809' },
  { code: 'DJ', name: 'Dżibuti', dial: '253' },
  { code: 'EG', name: 'Egipt', dial: '20' },
  { code: 'EC', name: 'Ekwador', dial: '593' },
  { code: 'ER', name: 'Erytrea', dial: '291' },
  { code: 'EE', name: 'Estonia', dial: '372' },
  { code: 'SZ', name: 'Eswatini', dial: '268' },
  { code: 'ET', name: 'Etiopia', dial: '251' },
  { code: 'FK', name: 'Falklandy', dial: '500' },
  { code: 'FJ', name: 'Fidżi', dial: '679' },
  { code: 'PH', name: 'Filipiny', dial: '63' },
  { code: 'FI', name: 'Finlandia', dial: '358' },
  { code: 'FR', name: 'Francja', dial: '33' },
  { code: 'GA', name: 'Gabon', dial: '241' },
  { code: 'GM', name: 'Gambia', dial: '220' },
  { code: 'GH', name: 'Ghana', dial: '233' },
  { code: 'GI', name: 'Gibraltar', dial: '350' },
  { code: 'GR', name: 'Grecja', dial: '30' },
  { code: 'GD', name: 'Grenada', dial: '1473' },
  { code: 'GL', name: 'Grenlandia', dial: '299' },
  { code: 'GE', name: 'Gruzja', dial: '995' },
  { code: 'GU', name: 'Guam', dial: '1671' },
  { code: 'GY', name: 'Gujana', dial: '592' },
  { code: 'GF', name: 'Gujana Francuska', dial: '594' },
  { code: 'GP', name: 'Gwadelupa', dial: '590' },
  { code: 'GT', name: 'Gwatemala', dial: '502' },
  { code: 'GN', name: 'Gwinea', dial: '224' },
  { code: 'GW', name: 'Gwinea Bissau', dial: '245' },
  { code: 'GQ', name: 'Gwinea Równikowa', dial: '240' },
  { code: 'HT', name: 'Haiti', dial: '509' },
  { code: 'ES', name: 'Hiszpania', dial: '34' },
  { code: 'NL', name: 'Holandia', dial: '31' },
  { code: 'HN', name: 'Honduras', dial: '504' },
  { code: 'HK', name: 'Hongkong', dial: '852' },
  { code: 'IN', name: 'Indie', dial: '91' },
  { code: 'ID', name: 'Indonezja', dial: '62' },
  { code: 'IQ', name: 'Irak', dial: '964' },
  { code: 'IR', name: 'Iran', dial: '98' },
  { code: 'IE', name: 'Irlandia', dial: '353' },
  { code: 'IS', name: 'Islandia', dial: '354' },
  { code: 'IL', name: 'Izrael', dial: '972' },
  { code: 'JM', name: 'Jamajka', dial: '1876' },
  { code: 'JP', name: 'Japonia', dial: '81' },
  { code: 'YE', name: 'Jemen', dial: '967' },
  { code: 'JO', name: 'Jordania', dial: '962' },
  { code: 'KY', name: 'Kajmany', dial: '1345' },
  { code: 'KH', name: 'Kambodża', dial: '855' },
  { code: 'CM', name: 'Kamerun', dial: '237' },
  { code: 'CA', name: 'Kanada', dial: '1' },
  { code: 'QA', name: 'Katar', dial: '974' },
  { code: 'KZ', name: 'Kazachstan', dial: '7' },
  { code: 'KE', name: 'Kenia', dial: '254' },
  { code: 'KG', name: 'Kirgistan', dial: '996' },
  { code: 'KI', name: 'Kiribati', dial: '686' },
  { code: 'CO', name: 'Kolumbia', dial: '57' },
  { code: 'KM', name: 'Komory', dial: '269' },
  { code: 'CG', name: 'Kongo', dial: '242' },
  { code: 'KR', name: 'Korea Południowa', dial: '82' },
  { code: 'KP', name: 'Korea Północna', dial: '850' },
  { code: 'CR', name: 'Kostaryka', dial: '506' },
  { code: 'CU', name: 'Kuba', dial: '53' },
  { code: 'KW', name: 'Kuwejt', dial: '965' },
  { code: 'LA', name: 'Laos', dial: '856' },
  { code: 'LS', name: 'Lesotho', dial: '266' },
  { code: 'LB', name: 'Liban', dial: '961' },
  { code: 'LR', name: 'Liberia', dial: '231' },
  { code: 'LY', name: 'Libia', dial: '218' },
  { code: 'LI', name: 'Liechtenstein', dial: '423' },
  { code: 'LT', name: 'Litwa', dial: '370' },
  { code: 'LU', name: 'Luksemburg', dial: '352' },
  { code: 'MK', name: 'Macedonia Północna', dial: '389' },
  { code: 'MG', name: 'Madagaskar', dial: '261' },
  { code: 'YT', name: 'Majotta', dial: '262' },
  { code: 'MO', name: 'Makau', dial: '853' },
  { code: 'MW', name: 'Malawi', dial: '265' },
  { code: 'MV', name: 'Malediwy', dial: '960' },
  { code: 'MY', name: 'Malezja', dial: '60' },
  { code: 'ML', name: 'Mali', dial: '223' },
  { code: 'MT', name: 'Malta', dial: '356' },
  { code: 'MP', name: 'Mariany Północne', dial: '1670' },
  { code: 'MA', name: 'Maroko', dial: '212' },
  { code: 'MQ', name: 'Martynika', dial: '596' },
  { code: 'MR', name: 'Mauretania', dial: '222' },
  { code: 'MU', name: 'Mauritius', dial: '230' },
  { code: 'MX', name: 'Meksyk', dial: '52' },
  { code: 'FM', name: 'Mikronezja', dial: '691' },
  { code: 'MM', name: 'Mjanma (Birma)', dial: '95' },
  { code: 'MC', name: 'Monako', dial: '377' },
  { code: 'MN', name: 'Mongolia', dial: '976' },
  { code: 'MS', name: 'Montserrat', dial: '1664' },
  { code: 'MZ', name: 'Mozambik', dial: '258' },
  { code: 'MD', name: 'Mołdawia', dial: '373' },
  { code: 'NA', name: 'Namibia', dial: '264' },
  { code: 'NR', name: 'Nauru', dial: '674' },
  { code: 'NP', name: 'Nepal', dial: '977' },
  { code: 'DE', name: 'Niemcy', dial: '49' },
  { code: 'NE', name: 'Niger', dial: '227' },
  { code: 'NG', name: 'Nigeria', dial: '234' },
  { code: 'NI', name: 'Nikaragua', dial: '505' },
  { code: 'NU', name: 'Niue', dial: '683' },
  { code: 'NF', name: 'Norfolk', dial: '672' },
  { code: 'NO', name: 'Norwegia', dial: '47' },
  { code: 'NC', name: 'Nowa Kaledonia', dial: '687' },
  { code: 'NZ', name: 'Nowa Zelandia', dial: '64' },
  { code: 'OM', name: 'Oman', dial: '968' },
  { code: 'PK', name: 'Pakistan', dial: '92' },
  { code: 'PW', name: 'Palau', dial: '680' },
  { code: 'PS', name: 'Palestyna', dial: '970' },
  { code: 'PA', name: 'Panama', dial: '507' },
  { code: 'PG', name: 'Papua-Nowa Gwinea', dial: '675' },
  { code: 'PY', name: 'Paragwaj', dial: '595' },
  { code: 'PE', name: 'Peru', dial: '51' },
  { code: 'PL', name: 'Polska', dial: '48' },
  { code: 'PR', name: 'Portoryko', dial: '1787' },
  { code: 'PT', name: 'Portugalia', dial: '351' },
  { code: 'ZA', name: 'Południowa Afryka', dial: '27' },
  { code: 'CV', name: 'Republika Zielonego Przylądka', dial: '238' },
  { code: 'CF', name: 'Republika Środkowoafrykańska', dial: '236' },
  { code: 'RE', name: 'Reunion', dial: '262' },
  { code: 'RU', name: 'Rosja', dial: '7' },
  { code: 'RO', name: 'Rumunia', dial: '40' },
  { code: 'RW', name: 'Rwanda', dial: '250' },
  { code: 'EH', name: 'Sahara Zachodnia', dial: '212' },
  { code: 'KN', name: 'Saint Kitts i Nevis', dial: '1869' },
  { code: 'LC', name: 'Saint Lucia', dial: '1758' },
  { code: 'VC', name: 'Saint Vincent i Grenadyny', dial: '1784' },
  { code: 'BL', name: 'Saint-Barthélemy', dial: '590' },
  { code: 'MF', name: 'Saint-Martin', dial: '590' },
  { code: 'PM', name: 'Saint-Pierre i Miquelon', dial: '508' },
  { code: 'SV', name: 'Salwador', dial: '503' },
  { code: 'WS', name: 'Samoa', dial: '685' },
  { code: 'AS', name: 'Samoa Amerykańskie', dial: '1684' },
  { code: 'SM', name: 'San Marino', dial: '378' },
  { code: 'SN', name: 'Senegal', dial: '221' },
  { code: 'RS', name: 'Serbia', dial: '381' },
  { code: 'SC', name: 'Seszele', dial: '248' },
  { code: 'SL', name: 'Sierra Leone', dial: '232' },
  { code: 'SG', name: 'Singapur', dial: '65' },
  { code: 'SX', name: 'Sint Maarten', dial: '1721' },
  { code: 'SO', name: 'Somalia', dial: '252' },
  { code: 'LK', name: 'Sri Lanka', dial: '94' },
  { code: 'US', name: 'Stany Zjednoczone', dial: '1' },
  { code: 'SD', name: 'Sudan', dial: '249' },
  { code: 'SS', name: 'Sudan Południowy', dial: '211' },
  { code: 'SR', name: 'Surinam', dial: '597' },
  { code: 'SJ', name: 'Svalbard i Jan Mayen', dial: '47' },
  { code: 'SY', name: 'Syria', dial: '963' },
  { code: 'CH', name: 'Szwajcaria', dial: '41' },
  { code: 'SE', name: 'Szwecja', dial: '46' },
  { code: 'SK', name: 'Słowacja', dial: '421' },
  { code: 'SI', name: 'Słowenia', dial: '386' },
  { code: 'TJ', name: 'Tadżykistan', dial: '992' },
  { code: 'TH', name: 'Tajlandia', dial: '66' },
  { code: 'TW', name: 'Tajwan', dial: '886' },
  { code: 'TZ', name: 'Tanzania', dial: '255' },
  { code: 'TG', name: 'Togo', dial: '228' },
  { code: 'TO', name: 'Tonga', dial: '676' },
  { code: 'TT', name: 'Trynidad i Tobago', dial: '1868' },
  { code: 'TN', name: 'Tunezja', dial: '216' },
  { code: 'TR', name: 'Turcja', dial: '90' },
  { code: 'TM', name: 'Turkmenistan', dial: '993' },
  { code: 'TC', name: 'Turks i Caicos', dial: '1649' },
  { code: 'TV', name: 'Tuvalu', dial: '688' },
  { code: 'UG', name: 'Uganda', dial: '256' },
  { code: 'UA', name: 'Ukraina', dial: '380' },
  { code: 'UY', name: 'Urugwaj', dial: '598' },
  { code: 'UZ', name: 'Uzbekistan', dial: '998' },
  { code: 'VU', name: 'Vanuatu', dial: '678' },
  { code: 'WF', name: 'Wallis i Futuna', dial: '681' },
  { code: 'VA', name: 'Watykan', dial: '379' },
  { code: 'VE', name: 'Wenezuela', dial: '58' },
  { code: 'GB', name: 'Wielka Brytania', dial: '44' },
  { code: 'VN', name: 'Wietnam', dial: '84' },
  { code: 'CI', name: 'Wybrzeże Kości Słoniowej', dial: '225' },
  { code: 'CX', name: 'Wyspa Bożego Narodzenia', dial: '61' },
  { code: 'IM', name: 'Wyspa Man', dial: '44' },
  { code: 'SH', name: 'Wyspa Świętej Heleny', dial: '290' },
  { code: 'AX', name: 'Wyspy Alandzkie', dial: '358' },
  { code: 'CK', name: 'Wyspy Cooka', dial: '682' },
  { code: 'VI', name: 'Wyspy Dziewicze (USA)', dial: '1340' },
  { code: 'VG', name: 'Wyspy Dziewicze (Wlk. Brytania)', dial: '1284' },
  { code: 'CC', name: 'Wyspy Kokosowe', dial: '61' },
  { code: 'MH', name: 'Wyspy Marshalla', dial: '692' },
  { code: 'FO', name: 'Wyspy Owcze', dial: '298' },
  { code: 'SB', name: 'Wyspy Salomona', dial: '677' },
  { code: 'ST', name: 'Wyspy Świętego Tomasza i Książęca', dial: '239' },
  { code: 'HU', name: 'Węgry', dial: '36' },
  { code: 'IT', name: 'Włochy', dial: '39' },
  { code: 'ZM', name: 'Zambia', dial: '260' },
  { code: 'ZW', name: 'Zimbabwe', dial: '263' },
  { code: 'AE', name: 'Zjednoczone Emiraty Arabskie', dial: '971' },
  { code: 'LV', name: 'Łotwa', dial: '371' },
]

const BY_CODE = new Map(COUNTRIES.map((c) => [c.code, c]))

/**
 * Zwraca informacje o państwie na podstawie dwuliterowego kodu ISO.
 *
 * @param code - Kod ISO kraju (np. 'PL', 'DE').
 * @returns Obiekt CountryDial lub undefined.
 */
export function getCountryByCode(code: string): CountryDial | undefined {
  return BY_CODE.get(code)
}

/**
 * Odnajduje kraj odpowiadający wpisanym cyfrom numeru kierunkowego.
 *
 * @param dialDigits - Cyfry kodu kierunkowego.
 * @returns Najlepiej dopasowany kraj.
 */
export function findCountryByDial(dialDigits: string): CountryDial | undefined {
  if (dialDigits.startsWith('48')) {
    return BY_CODE.get('PL')
  }
  let best: CountryDial | undefined
  for (const country of COUNTRIES) {
    if (!dialDigits.startsWith(country.dial)) continue
    if (!best || country.dial.length > best.dial.length) {
      best = country
    }
  }
  return best
}

/**
 * Formatuje reprezentację kraju do wyboru na liście rozwijanej.
 *
 * @param country - Obiekt z danymi kraju.
 * @returns Sformatowany napis, np. "Polska (+48)".
 */
export function formatCountryOption(country: CountryDial): string {
  return `${country.name} (+${country.dial})`
}

