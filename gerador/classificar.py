"""Classify Yupoo album titles into team / league / kit type / sizes (PT + ZH titles)."""
import re
import unicodedata

MAIN = [("Jacket", "Jaqueta", "夹克"), ("Hoodie", "Moletom", "卫衣"), ("Polo", "Camisa Polo", "Polo衫"),
        ("GK", "Camisa de Goleiro", "守门员球衣"), ("Training", "Camisa de Treino", "训练服"),
        ("Retro", "Camisa Retrô", "复古球衣"), ("Special", "Camisa Edição Especial", "特别版球衣"),
        ("Fourth", "Camisa 4", "第四客场球衣"), ("Third", "Camisa 3", "第三客场球衣"),
        ("Away", "Camisa 2", "客场球衣"), ("Home", "Camisa 1", "主场球衣")]
EN = {"Polo": "Polo Shirt", "GK": "Goalkeeper Jersey", "Training": "Training Jersey", "Retro": "Retro Jersey",
      "Special": "Special Edition Jersey", "Fourth": "Fourth Jersey", "Third": "Third Jersey",
      "Away": "Away Jersey", "Home": "Home Jersey"}  # Jacket/Hoodie: a própria chave
QUAL = [("Player", "Jogador", "球员版"), ("Kids", "Infantil", "儿童"), ("Women", "Feminina", "女款"),
        ("Long sleeve", "Manga Longa", "长袖"), ("World Cup", "Copa do Mundo", "世界杯")]

# synonyms per kit type / qualifier (regex on the normalized, lowercase title)
KIT_RE = {
    "Jacket": r"jackets?|windbreakers?|coats?|trench|夹克|外套|风衣",
    "Hoodie": r"hoodies?|hooded sweat\w*|sweatshirts?|pullover|卫衣",
    "Polo": r"polos?|polo衫",
    "GK": r"goalie|goal ?keepe\w*|goal ?kee\w*|keepers?|gk|门将|守门员",
    "Training": r"training|pre ?match|warm ?up|训练",
    "Retro": r"retro|classics?|vintage|reissue|throwback|复古",
    "Special": r"special|limited|commemorative|edition|anniversary|signed|joint|souvenir|memorial|特别|纪念",
    "Fourth": r"fou?rth(ly)?|4th|第四",
    "Third": r"thi?rd|3rd|second ?away|二客|第三",
    "Away": r"away|second|2nd|客场|客",
    "Home": r"home|主场|主",
}
# peças de baixo: vencem o tipo de camisa (exceto jaqueta/moletom, que podem vir com calça)
# "short" sozinho não entra: "Short Women's Jersey" é camisa feminina curta
BOTTOM = [("Short", "短裤", "Shorts", r"shorts|calc(ao|oes)|bermudas?|短裤|单裤|球裤"),
          ("Calça", "长裤", "Pants", r"pants|trousers|joggers?|calcas?|长裤|裤子|卫裤|运动裤|紧身裤")]
SIDE = {"Home": ("1", "主场", "Home"), "Away": ("2", "客场", "Away"), "Third": ("3", "第三客场", "Third"),
        "Fourth": ("4", "第四客场", "Fourth")}
QUAL_RE = {
    "Player": r"play?e?rs?|球员",
    "Kids": r"kids?|child(ren)?|baby|youth|boys?|儿童|童装|孩子|童",
    "Women": r"women\w*|woman|female|femin\w*|ladies|lady|女",
    "Long sleeve": r"lo+n?g[ -]?sl?e\w*|长袖",
    "World Cup": r"world ?cup|世界杯",
}

# --- team table: "Name = alias, alias" (aliases lowercase/unaccented; the name itself is added) ---
RAW = """
@brasileirao
Flamengo = fla, 弗拉门戈
Fluminense = fluminen, minense, fruimense, 弗鲁米嫩塞
Palmeiras = 帕尔梅拉斯
Corinthians = 科林蒂安
São Paulo = sao paulo, 圣保罗
Santos = 桑托斯
Grêmio = 格雷米奥
Internacional = sc internacional, 国际体育会
Atlético Mineiro = atletico mineiro, atletico mg, atletico mg, mineiro, 米内罗竞技
Atlético Paranaense = athletico paranaense, athletico pr, athletico, atletico paranaense
Cruzeiro = 克鲁塞罗
Botafogo = 博塔弗戈
Vasco da Gama = vasco, 瓦斯科
Bahia = 巴伊亚
Fortaleza = 福塔雷萨
Bragantino = red bull bragantino, rb bragantino
Coritiba = 科里蒂巴
Avaí = avai
Vitória = vitoria, vitoria ba
Sport Recife = sport recife, sport club recife
Chapecoense = chapecoense
Paysandu = paysandu
Santa Cruz = santa cruz
Ceará = ceara
Goiás = goias
Juventude = juventude
Mirassol = mirassol
Remo = remo
Criciúma = criciuma
Cuiabá = cuiaba
América Mineiro = america mineiro, america mg
Operário = operario
Ponte Preta = ponte preta
Guarani = guarani
Náutico = nautico
@premier
Arsenal = 阿森纳, gunners
Aston Villa = villa, 阿斯顿维拉
Chelsea = 切尔西
Liverpool = 利物浦, 利物普
Manchester City = man city, mancity, man c, 曼城
Manchester United = man u, ma u, manu, m u, man utd, man united, manchester utd, 曼联
Tottenham = spurs, tottenham hotspur, 热刺
Newcastle United = newcastle, 纽卡斯尔, 纽卡
West Ham = west ham united, 西汉姆
Wolves = wolverhampton, wolverhampton wanderers, 狼队
Everton = 埃弗顿
Brighton = brighton hove albion, 布莱顿
Brentford = 布伦特福德
Fulham = 富勒姆
Crystal Palace = palace, 水晶宫
Bournemouth = 伯恩茅斯
Nottingham Forest = nottingham, forest, nottm forest, 诺丁汉森林
Leeds United = leeds, 利兹联
Leicester City = leicester, 莱斯特城
Southampton = 南安普顿
Burnley = 伯恩利
Sunderland = 桑德兰
Sheffield United = sheffield utd, sheff utd
Sheffield Wednesday = sheffield wed
Ipswich Town = ipswich
Luton Town = luton
Norwich City = norwich
Watford = watford
West Bromwich Albion = west brom, west bromwich
Middlesbrough = boro
Stoke City = stoke
Blackburn Rovers = blackburn
Birmingham City = birmingham
Bolton Wanderers = bolton
Bristol City = bristol city
Charlton Athletic = charlton
Coventry City = coventry
Derby County = derby
Doncaster Rovers = doncaster
Hull City = hull
Huddersfield Town = huddersfield
Millwall = millwall
Northampton Town = northampton
Oxford United = oxford
Plymouth Argyle = plymouth
Portsmouth = portsmouth
Preston North End = preston
Reading = reading
Swansea City = swansea
Walsall = walsall
Wrexham = wrexham
Wycombe Wanderers = wycombe
Queens Park Rangers = qpr
Cardiff City = cardiff
Blackpool = blackpool
Wigan Athletic = wigan
Barnsley = barnsley
Rotherham United = rotherham
Stockport County = stockport
Lincoln City = lincoln
Peterborough United = peterborough
@laliga
Real Madrid = real madrid, madrid, 皇马, 皇家马德里
Barcelona = barca, 巴萨, 巴塞罗那
Atlético de Madrid = atletico madrid, atletico de madrid, atletico, atleti, 马竞, 马德里竞技
Sevilla = seville, 塞维利亚
Valencia = 瓦伦西亚
Villarreal = villareal, 比利亚雷亚尔
Real Betis = betis, 贝蒂斯
Real Sociedad = sociedad, 皇家社会
Athletic Bilbao = athletic club, bilbao, 毕尔巴鄂
Celta Vigo = celta, 塞尔塔
Getafe = 赫塔菲
Girona = 赫罗纳
Osasuna = 奥萨苏纳
Mallorca = 马略卡
Rayo Vallecano = rayo, 巴列卡诺
Alaves = 阿拉维斯
Las Palmas = 拉斯帕尔马斯
Cadiz = 加的斯
Granada = 格拉纳达
Elche = elche
Espanyol = espanyol
Real Valladolid = valladolid
Leganes = leganes
Levante = levante
Real Oviedo = oviedo
Real Zaragoza = zaragoza
Real Murcia = murcia
Malaga = malaga
Deportivo La Coruna = deportivo, depor, la coruna
Racing Santander = racing santander
Castellon = cd castellon
Albacete = albacete
Burgos = burgos
Tenerife = tenerife
Sporting Gijon = gijon
Eibar = eibar
Almeria = almeria
@seriea
AC Milan = ac milan, ac, milan, 米兰, ac米兰
Inter Milan = inter, internazionale, 国米, 国际米兰
Juventus = juve, 尤文, 尤文图斯
Napoli = naples, 那不勒斯
Roma = as roma, 罗马
Lazio = 拉齐奥
Atalanta = 亚特兰大
Fiorentina = 佛罗伦萨
Bologna = 博洛尼亚
Torino = 都灵
Genoa = 热那亚
Sampdoria = 桑普多利亚
Udinese = 乌迪内斯
Sassuolo = sassuolo
Cagliari = 卡利亚里
Lecce = lecce
Parma = parma
Como = como
Monza = monza
Hellas Verona = verona, hellas
Empoli = empoli
Venezia = venice
Cremonese = cremonese
Palermo = palermo
Bari = bari
Salernitana = salernitana
Ravenna = ravenna
Sorrento = sorrento
Spezia = spezia
Pisa = pisa
Brescia = brescia
Cesena = cesena
Catania = catania
Reggina = reggina
Modena = modena
@bundesliga
Bayern Munich = bayern, munich, 拜仁, 拜仁慕尼黑
Borussia Dortmund = dortmund, bvb, 多特蒙德, 多特
Bayer Leverkusen = leverkusen, 勒沃库森
RB Leipzig = leipzig, 莱比锡
Eintracht Frankfurt = frankfurt, 法兰克福
Wolfsburg = 沃尔夫斯堡
Borussia Monchengladbach = gladbach, monchengladbach, mgladbach, m gladbach
Werder Bremen = bremen, werder, 云达不莱梅
VfB Stuttgart = stuttgart, 斯图加特
Freiburg = freiburg
Hoffenheim = hoffenheim
Mainz 05 = mainz
Augsburg = augsburg
Union Berlin = union berlin
Hertha Berlin = hertha
St. Pauli = st pauli, st pauli, sankt pauli
Schalke 04 = schalke
Hamburger SV = hamburg, hsv
FC Koln = koln, cologne
Heidenheim = heidenheim
Holstein Kiel = kiel
Bochum = bochum
Darmstadt = darmstadt
Hannover 96 = hannover
Nuremberg = nurnberg
Fortuna Dusseldorf = dusseldorf
Kaiserslautern = kaiserslautern
Karlsruhe = karlsruhe
Dynamo Dresden = dresden
Hansa Rostock = rostock
Arminia Bielefeld = bielefeld
Preussen Munster = munster
Paderborn = paderborn
Magdeburg = magdeburg
@ligue1
Paris Saint-Germain = paris saint germain, paris, psg, 巴黎, 巴黎圣日耳曼
Marseille = olympique marseille, 马赛
Lyon = lyonnais, olympique lyonnais, 里昂
Monaco = 摩纳哥
Lille = lille
Nice = 尼斯
Lens = lens
Rennes = rennes
Nantes = nantes
Strasbourg = strasbourg
Toulouse = toulouse
Montpellier = montpellier
Reims = reims
Brest = brest
Auxerre = auxerre
Angers = angers
Le Havre = le havre
Metz = metz
Saint-Etienne = saint etienne, st etienne
Bordeaux = bordeaux
Lorient = lorient
Clermont = clermont
@portugal
Benfica = 本菲卡
Porto = 波尔图
Sporting CP = sporting cp, sporting lisbon, sporting, 里斯本竞技
Braga = 布拉加
Vitoria Guimaraes = guimaraes, vitoria sc
Casa Pia = casa pia
Famalicao = famalicao
Boavista = boavista
Estoril = estoril
Gil Vicente = gil vicente
Rio Ave = rio ave
Moreirense = moreirense
Arouca = arouca
Nacional Madeira = nacional madeira
@argentina
Boca Juniors = boca, 博卡青年, 博卡
River Plate = river, 河床
Racing Club = racing club
Estudiantes = estudiantes
Lanus = lanus
Newell's Old Boys = newell s old boys, newells, newell s
Independiente = independiente
San Lorenzo = san lorenzo
Velez Sarsfield = velez
Rosario Central = rosario central
Talleres = talleres
Huracan = huracan
Argentinos Juniors = argentinos juniors
Banfield = banfield
Gimnasia = gimnasia
Belgrano = belgrano
Godoy Cruz = godoy cruz
Platense = platense
@liga-mx
Club America = america, club america, 美洲, 美洲鹰
Chivas = guadalajara, chivas, 瓜达拉哈拉
Cruz Azul = blue cross, 蓝十字
Pumas UNAM = pumas, unam, 美洲狮
Tigres UANL = tigres, uanl, 老虎
Monterrey = rayados, 蒙特雷
Toluca = 托卢卡
Pachuca = 帕丘卡
Leon = club leon
Atlas = atlas
Tijuana = xolos, 蒂华纳
Santos Laguna = santos laguna
Necaxa = necaxa
Puebla = puebla
Queretaro = queretaro
Juarez = fc juarez, juarez
Mazatlan = mazatlan
Atletico San Luis = atletico san luis, san luis
@mls
Inter Miami = miami, 迈阿密国际, 迈阿密
LA Galaxy = galaxy, la galaxy, 洛杉矶银河
LAFC = lafc, los angeles fc
Atlanta United = atlanta united
Seattle Sounders = seattle
Portland Timbers = portland
New York City FC = new york city, nycfc, nyc fc
New York Red Bulls = new york red bulls, ny red bulls
Toronto FC = toronto
Vancouver Whitecaps = vancouver
CF Montreal = montreal
Chicago Fire = chicago fire
Philadelphia Union = philadelphia union
Charlotte FC = charlotte
Orlando City = orlando city
Columbus Crew = columbus crew
DC United = dc united
FC Dallas = fc dallas
Houston Dynamo = houston dynamo
Minnesota United = minnesota united
Nashville SC = nashville
New England Revolution = new england revolution
Real Salt Lake = real salt lake
San Jose Earthquakes = san jose earthquakes
Sporting Kansas City = sporting kansas city
Austin FC = austin fc
@saudi
Al Hilal = hilal, new moon, 新月
Al Nassr = nassr, 利雅得胜利, 胜利
Al Ittihad = ittihad, 吉达联合
Al Ahli = al ahli, ahli saudi, 吉达国民
Al Shabab = al shabab
Al Ettifaq = ettifaq
Al Fateh = al fateh
Al Qadsiah = qadsiah
Saudi Club = saudi club, saudi
@outras-ligas
Ajax = 阿贾克斯
PSV = psv eindhoven, 埃因霍温
Feyenoord = 费耶诺德
Twente = twente
Utrecht = utrecht
Heerenveen = heerenveen
AZ Alkmaar = az alkmaar
Celtic = 凯尔特人
Rangers = glasgow rangers, 流浪者, rangers fc
Aberdeen = aberdeen
Heart of Midlothian = hearts, heart of midlothian
Hibernian = hibernian, hibs
Galatasaray = 加拉塔萨雷
Fenerbahce = 费内巴切
Besiktas = 贝西克塔斯
Trabzonspor = trabzonspor
Club Brugge = brugge, club brugge
Anderlecht = anderlecht
Genk = genk
Dinamo Zagreb = dinamo zagreb
Red Star Belgrade = red star, crvena zvezda
Partizan = partizan
Red Bull Salzburg = salzburg, red bull salzburg
Sturm Graz = sturm graz
Rapid Vienna = rapid wien, rapid vienna
Shakhtar Donetsk = shakhtar
Dynamo Kyiv = dynamo kyiv, dynamo kiev
Olympiacos = olympiacos
Panathinaikos = panathinaikos
PAOK = paok
AEK Athens = aek
FC Copenhagen = copenhagen
Malmo = malmo
Servette = servette
Young Boys = young boys
Basel = basel
Legia Warsaw = legia
Al Ahly = al ahly, ahly, 阿赫利
Zamalek = zamalek
Alianza Lima = alianza lima
Cerro Porteno = cerro porteno
Nacional = nacional
Penarol = penarol
Colo-Colo = colo colo
Universidad de Chile = universidad de chile, u de chile
Junior Barranquilla = junior barranquilla
Bohemians = bohemian, bohemians
Olimpia = olimpia
Libertad = libertad
Atletico Nacional = atletico nacional
Millonarios = millonarios
Barcelona SC = barcelona sc, barcelona guayaquil
LDU Quito = ldu
Vissel Kobe = vissel kobe
Urawa Reds = urawa
Al Duhail = al duhail
Persepolis = persepolis
@selecoes
Brasil = brazil, brazilian, 巴西
Argentina = argentine, argentinian, 阿根廷
França = france, french, 法国
Alemanha = germany, german, 德国
Inglaterra = england, english, 英格兰
Espanha = spain, spanish, 西班牙
Itália = italy, italian, 意大利
Portugal = portuguese, 葡萄牙
Holanda = netherlands, holland, dutch, 荷兰
México = mexico, mexican, 墨西哥
Estados Unidos = usa, united states, usmnt, america usa, 美国
Japão = japan, japanese, 日本
Bélgica = belgium, 比利时
Croácia = croatia, 克罗地亚
Uruguai = uruguay, 乌拉圭
Colômbia = colombia, 哥伦比亚
Equador = ecuador
Chile = chile, 智利
Peru = peru
Paraguai = paraguay
Bolívia = bolivia
Venezuela = venezuela
Canadá = canada, canadian
Marrocos = morocco
Senegal = senegal
Nigéria = nigeria
Gana = ghana
Camarões = cameroon
Costa do Marfim = ivory coast, cote d ivoire
Tunísia = tunisia
Argélia = algeria
Egito = egypt
África do Sul = south africa
Cabo Verde = cape verde
Mali = mali
Comores = comoros
RD Congo = dr congo, congo
Coreia do Sul = south korea, korea, 韩国
Austrália = australia
Irã = iran
Iraque = iraq
Arábia Saudita = saudi arabia
Catar = qatar
Jordânia = jordan
Uzbequistão = uzbekistan
Emirados Árabes = uae, united arab emirates
Indonésia = indonesia
Malásia = malaysia
Filipinas = philippines
Nova Zelândia = new zealand
Dinamarca = denmark, danish
Suécia = sweden, swedish
Noruega = norway
Finlândia = finland
Islândia = iceland
Suíça = switzerland, swiss
Áustria = austria
Polônia = poland
República Tcheca = czech republic, czech, czechia
Hungria = hungary
Grécia = greece
Turquia = turkey, turkiye
Ucrânia = ukraine
Escócia = scotland, scottish
País de Gales = wales, welsh
Irlanda = ireland, irish
Albânia = albania
Bósnia = bosnia
Eslovênia = slovenia
Sérvia = serbia
Romênia = romania
Eslováquia = slovakia
Israel = israel
Palestina = palestine
Haiti = haiti
Jamaica = jamaica
Panamá = panama
Costa Rica = costa rica
Guatemala = guatemala
Honduras = honduras
El Salvador = el salvador
Curaçao = curacao
China = china, 中国
Gabão = gabon
Trinidad e Tobago = trinidad
@brasileirao
Flamengo = flamenco, framenco, flamingo
Fluminense = furiminese, fornirense, furiminense
Palmeiras = palmelas, panimelas, palmeira
Corinthians = corinthian
Paysandu = paisandu, paisanse
Atlético Mineiro = minero
Botafogo = bodafogo
Chapecoense = chapeco
Sport Recife = recife
Vasco da Gama = vasco da gama rj
@premier
Queens Park Rangers = queen park rangers, queens park rangers, qpr
Tottenham = tottenham hotspur
Sheffield United = sheffield, saffield
Sheffield Wednesday = wednesday
Derby County = derbyshire
Bournemouth = bernmouth, bournemouth
Leicester City = brecester
Manchester City = manchester
Manchester United = man utraining
Aston Villa = aston
Doncaster Rovers = tancaster
Bristol City = bristol, bristol rovers
West Bromwich Albion = midderfield
Charlton Athletic = charlton athletic
@laliga
Alaves = alavis
Getafe = hetafe, hectafei, hetaa
Burgos = bolgos, borogos
Real Oviedo = ovidio
Racing Santander = santander
Rayo Vallecano = balecano
Barcelona = barcellana
Cadiz = gads
@seriea
Roma = rome, roman
Fiorentina = florence
Torino = turin
Napoli = neapolitan
Salernitana = sarernitana
Lecce = lecce
@bundesliga
Union Berlin = berlin united
Schalke 04 = schalke
TSV 1860 Munich = tsv 1860, 1860 munchen, 1860 munich
Arminia Bielefeld = bielefelder
Bayern Munich = munching
Holstein Kiel = holsteinkiel, holstekiel
Nuremberg = nulenberg
Borussia Monchengladbach = moenshing
Hannover 96 = hanover
Kaiserslautern = kaiserlautern
@ligue1
Lens = lons
Le Havre = havre
Rennes = rennais, stade rennais
Lyon = lyons
@portugal
Benfica = lisbon
Casa Pia = nicasa
@liga-mx
Tigres UANL = tiger, tigers
Club America = americas
Pumas UNAM = cougar, cougars
Cruz Azul = cruzero, cruisersro
Toluca = torulca, toluctraining
Monterrey = monterey
Pachuca = pacachu
@argentina
River Plate = riverbed
Racing Club = racing
Estudiantes = la plata university students
Lanus = lans
@mls
Atlanta United = atlanta
Philadelphia Union = philadelphia
Chicago Fire = chicago
LAFC = los angeles
@saudi
Al Nassr = riyadh
Al Hilal = crescent moon
@outras-ligas
Celtic = celtics
Colo-Colo = colocolo
PSV = eindhoven
Junior Barranquilla = barranquilla
Galatasaray = galata
Servette = geneva
Club Brugge = bruges
Sturm Graz = graz
Dinamo Zagreb = dinamo
Rangers = ranger
Alianza Lima = alliance lima
Universidad Católica = catholic
Universidad de Chile = university of chile
Colo-Colo = colo colot
Alianza Lima = lima league
@selecoes
Estados Unidos = american, americans
Argélia = algerian
Colômbia = columbia, colombian
Palestina = palestinian, palestinians
Austrália = australian
Noruega = norwegian
Tunísia = tunisian
Haiti = haitian
Filipinas = philippine
Bélgica = belgian
Grécia = greek
Áustria = austrian
Uruguai = uruguayan
Nigéria = nigerian
Coreia do Sul = korean
Comores = comoro, comoran
Espanha = spaniards
Polônia = polish
Croácia = croatian
Gana = ghanaian
Marrocos = moroccan
Egito = egyptian
Irã = iranian
Iraque = iraqi
Turquia = turkish
Ucrânia = ukrainian
Venezuela = venezuelan
Peru = peruvian
Chile = chilean
Equador = ecuadorian
Bolívia = bolivian
Paraguai = paraguayan
Panamá = panamanian
Jamaica = jamaican
Catar = qatari
Jordânia = jordanian
Camarões = cameroonian
Costa do Marfim = ivorian
Mali = malian
África do Sul = south african
Suécia = swedes
Finlândia = finnish
Islândia = icelandic
Hungria = hungarian
Eslováquia = slovak
Sérvia = serbian
Romênia = romanian
Bósnia = bosnian
Albânia = albanian
Eslovênia = slovenian
Costa Rica = costa rican
Guatemala = guatemalan
Honduras = honduran
Indonésia = indonesian
Malásia = malaysian
Israel = israeli
Nova Zelândia = new zealander
"""

_CJK = r"一-鿿"


def _norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[‐-―−]", "-", s)
    s = re.sub(rf"(?<=[{_CJK}])\s+(?=[{_CJK}])", "", s)  # "利 物 浦" -> "利物浦"
    return s


def _alias_norm(s):
    s = _norm(s).strip()
    return s if re.search(rf"[{_CJK}]", s) else re.sub(r"[^a-z0-9]+", " ", s).strip()


ALIASES = {}  # normalized alias -> (display name, league)
_lg = None
for _line in RAW.strip().splitlines():
    if _line.startswith("@"):
        _lg = _line[1:]
        continue
    _n, _, _al = _line.partition(" = ")
    for _a in [_n] + _al.split(","):
        _a = _alias_norm(_a)
        if _a:
            ALIASES.setdefault(_a, (_n, _lg))
WEAK = {"jordan", "us"}  # only used when nothing else matches (e.g. "Paris Jordan")
ALIASES["us"] = ("Estados Unidos", "selecoes")
_SORTED = sorted(ALIASES, key=len, reverse=True)
_ASCII = re.compile(r"^[a-z0-9 ]+$")


def _find_team(title):
    t = _norm(title)
    t = re.sub(r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", t)  # "24/25Arsenal"
    text = " " + re.sub(r"[^a-z0-9" + _CJK + r"]+", " ", t).strip() + " "
    for weak in (False, True):  # weak aliases only when nothing else matches
        best = None
        for a in _SORTED:
            if (a in WEAK) != weak:
                continue
            if best and len(a) < best[0]:
                break
            pos = text.find(f" {a} ") if _ASCII.match(a) else text.find(a)
            if pos >= 0 and (not best or (len(a), -pos) > best[:2]):
                best = (len(a), -pos, a)
        if best:
            return ALIASES[best[2]]
    return None


# --- season ---
_SEP = r"\s*[-/~]\s*"
_PRE = r"(?<![A-Za-z\d])"


def _season(title):
    """Return (season string or '', start year or None)."""
    t = re.sub(r"[‐-―−]", "-", title)
    m = re.search(_PRE + r"(?:20|19)?(\d{2})" + _SEP + r"(?:20|19)?(\d{2})(?!\d)", t)
    if m and int(m[2]) == (int(m[1]) + 1) % 100:
        a = int(m[1])
        return f"{a:02d}/{int(m[2]):02d}", (1900 + a if a >= 50 else 2000 + a)
    m = re.search(_PRE + r"(\d{2})(\d{2})(?!\d)", t)
    if m and int(m[2]) == int(m[1]) + 1 and 5 <= int(m[1]) <= 40:
        return f"{m[1]}/{m[2]}", 2000 + int(m[1])
    m = re.search(_PRE + r"(19\d{2}|20\d{2})(?!\d)", t)
    if m:
        return m[1], int(m[1])
    m = re.match(r"\s*(\d{2})-(?=[A-Za-z])", t)  # "26-Man U Special Edition"
    if m:
        a = int(m[1])
        return f"{a:02d}/{a + 1:02d}", 2000 + a
    return "", None


# --- sizes ---
SIZES = ["S", "M", "L", "XL", "2XL", "3XL", "4XL"]
_SZ = r"(XXXXL|XXXL|XXL|XL|[234] ?XL|XS|S|M|L)"
_SZ_ALIAS = {"XS": "S", "XXL": "2XL", "XXXL": "3XL", "XXXXL": "4XL"}


def _sz(x):
    x = x.upper().replace(" ", "")
    return _SZ_ALIAS.get(x, x)


def _sizes(title, kids):
    if kids:
        ms = re.findall(r"(?<!\d)(1[6-9])\s*#?\s*[-~—]+\s*#?(1[6-9]|2\d|30)(?!\d)", title)
        mx = int(ms[-1][1]) if ms else 28  # last match: the first one may be the season
        return [str(i) for i in range(16, max(mx, 16) + 1, 2)]
    ms = re.findall(r"(?<![A-Za-z'])" + _SZ + r"\s*[-~—–一to]+\s*" + _SZ + r"(?![A-Za-z])", title, re.I)
    if ms:
        a, b = (_sz(x) for x in ms[-1])
        if a in SIZES and b in SIZES and SIZES.index(a) <= SIZES.index(b):
            return SIZES[SIZES.index(a): SIZES.index(b) + 1]
    return SIZES[:6 - 1]  # S..2XL


def _has(pat, t):
    # CJK alternatives match anywhere; latin ones need word-ish boundaries
    return re.search(rf"(?<![a-z])(?:{pat})(?![a-z])", t) is not None


def _kit(raw):
    t = _norm(raw)
    t = re.sub(rf"(?<=[{_CJK}])(?=[a-z0-9])|(?<=[a-z0-9])(?=[{_CJK}])", " ", t)  # "短裤S" -> "短裤 s": senão a borda latina falha
    return re.sub(r"[^a-z0-9#" + _CJK + r"]+", " ", t)


def _build(title, n, league, forced_retro=False):
    t = _kit(title)
    season, year = _season(title)
    kids = _has(QUAL_RE["Kids"], t) or bool(re.search(r"(?<!\d)16\s*#?\s*[-~]+\s*#?(2\d|30)(?!\d)", title))
    qual = {q: (kids if q == "Kids" else _has(QUAL_RE[q], t)) for q, *_ in QUAL}
    ts = re.sub(r"players?( s)?\s*(edition|version)", " ", t)  # "Player Edition" is not "Special"
    found = {k: _has(KIT_RE[k], ts) for k, *_ in MAIN}
    retro = forced_retro or found["Retro"] or (year is not None and year < 2015)
    found["Retro"] = retro
    main = next(((pt, zh, EN.get(k, k)) for k, pt, zh in MAIN if found[k]), ("Camisa", "球衣", "Jersey"))
    bottom = next((b for b in BOTTOM if _has(b[3], ts)), None)
    if bottom and not (found["Jacket"] or found["Hoodie"]):
        side = next((SIDE[k] for k in ("Fourth", "Third", "Away", "Home") if found[k]), None)
        main = (f"{bottom[0]} {side[0]}" if side else bottom[0], (side[1] if side else "") + bottom[1],
                (side[2] + " " if side else "") + bottom[2])
    qs = [(pt, zh, k.title()) for k, pt, zh in QUAL if qual[k]]
    return {
        "n": n, "l": "retro" if retro else league,
        "t": f"{main[0]} {n}" + (f" {season}" if season else ""),
        "tz": f"{n} " + (season + " " if season else "") + main[1],
        "te": f"{n} " + (season + " " if season else "") + main[2],
        "q": " · ".join(q[0] for q in qs), "qz": " · ".join(q[1] for q in qs), "qe": " · ".join(q[2] for q in qs),
        "s": _sizes(title, kids),
        **({"sh": 1} if bottom else {}),  # short/calça fica fora da vitrine da home
    }


def classify(title):
    """Return the classification dict, or None when no known team/country is found."""
    hit = _find_team(title)
    if not hit:
        return None
    return _build(title, *hit)


def _clean(title):
    s = re.sub(r"https?://\S+", " ", title)
    s = re.sub(_PRE + r"(?:20|19)?\d{2}\s*[-/~]\s*(?:20|19)?\d{2}(?!\d)|" + _PRE + r"(?:19|20)\d{2}(?!\d)", " ", s)
    s = re.sub(r"[\s,]*#?\d*" + _SZ + r"?\s*[-~—–]\s*#?\d*" + _SZ + r"?\s*$", " ", s, flags=re.I)
    s = re.sub(r"\b(" + "|".join(v for d in (KIT_RE, QUAL_RE) for v in d.values() if v.isascii()) + r")\b", " ", s, flags=re.I)
    s = re.sub(r"[\s\-:,]+", " ", s).strip(" -:,")
    return s or "Outros"


def classify_all(items):
    """Classify every item ({'t','img','h'}); unknown ones become league 'outros' (or 'retro')."""
    out = []
    for it in items:
        c = classify(it["t"])
        if c is None:
            c = _build(it["t"], _clean(it["t"]), "outros")
        out.append({**c, "h": it["h"]})
    return out


if __name__ == "__main__":
    def t(title):
        return classify(title)
    assert t("26-27阿森纳客短裤S一2XL")["t"] == "Short 2 Arsenal 26/27"
    assert t("26-27阿森纳客短裤S一2XL")["te"] == "Arsenal 26/27 Away Shorts"
    assert t("26-27阿斯顿维拉主场单裤S一3XL")["t"] == "Short 1 Aston Villa 26/27"
    assert t("26-27阿斯顿维拉主场单裤S一3XL")["s"][-1] == "3XL"
    assert t("26.皇马长裤S一3XL")["t"] == "Calça Real Madrid"
    assert t("26-27迈阿密客场单裤S一3XL")["n"] == "Inter Miami"
    assert t("Barcelona 25/26 Home Shorts S-XXL")["t"] == "Short 1 Barcelona 25/26"
    assert t("Barcelona 25/26 Home Shorts S-XXL")["sh"] == 1
    assert t("Short Women's 2026/27 Flamengo Away Jersey S-XXL")["t"] == "Camisa 2 Flamengo 26/27"
    assert "sh" not in t("Short Women's 2026/27 Flamengo Away Jersey S-XXL")
    assert t("Windbreaker Fluminense red pants S-XXL")["t"].startswith("Jaqueta")
    assert t("25/26 Flamengo training pants S-XXL")["t"] == "Calça Flamengo 25/26"
    print("ok")
