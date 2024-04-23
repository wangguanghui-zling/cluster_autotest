#! /usr/bin/env python



"""
store language mapping table, these languages are available for tesseract5.0
"""


from enum import Enum


class BaiDuLang(Enum):
	Chinese = "CHN_ENG"
	English = "ENG"
	Japanese = "JAP"
	Korean = "KOR"
	French = "FRE"
	Spanish = "SPA"
	Portuguese = "POR"
	German = "GER"
	Italian = "ITA"
	Russian = "RUS"


class Lang(Enum):
	Chinese = "chi_sim"  # - Simplified(中国 - 简体)
	ChineseTraditional = "chi_tra"  # (中国 - 繁体)
	English = "eng"  # 英语
	Afrikaans = "afr"  # 南非荷兰语
	Amharic = "amh"  # 阿姆哈拉语
	Arabic = "ara"  # 阿拉伯语
	Assamese = "asm"  # (阿萨姆)
	Azerbaijani = "aze"  # (阿塞拜疆)
	AzerbaijaniCyrilic = "aze_cyrl"  # (阿塞拜疆 - Cyrilic)
	Belarusian = "bel"  # (白俄罗斯)
	Bengali = "ben"  # (孟加拉)
	Tibetan = "bod"  # (西藏)
	Bosnian = "bos"  # (波斯尼亚)
	Bulgarian = "bul"  # (保加利亚语)
	CatalanValencian = "cat"  # (加泰罗尼亚语;巴伦西亚)
	Cebuano = "ceb"  # (宿务)
	Czech = "ces"  # (捷克)
	Cherokee = "chr"  # (切诺基)
	Welsh = "cym"  # (威尔士)
	Danish = "dan"  # (丹麦)
	DanishFraktur = "dan_frak"  # (丹麦 - Fraktur)
	German = "deu"  # (德国)
	GermanFraktur = "deu_frak"  # (德国 - Fraktur)
	Dzongkha = "dzo"  # (不丹文)
	Greek = "ell"  # Modern （1453 -）(希腊，现代（1453-）)
	EnglishMiddle = "enm"  # (1100 - 1500)(英语，中东（1100 - 1500）)
	Esperanto = "epo"  # (世界语)
	Math = "equ"  # Math/ equation detection module(数学 / 方程式检测模块)
	Estonian = "est"  # (爱沙尼亚)
	Basque = "eus"  # (巴斯克)
	Persian = "fas"  # (波斯)
	Finnish = "fin"  # (芬兰)
	French = "fra"  # (法语)
	Frankish = "frk"  # (法兰克)
	FrenchMiddle = "frm"  # (ca.1400 - 1600)(法国，中东（ca.1400-1600）)
	Irish = "gle"  # (爱尔兰)
	Galician = "glg"  # (加利西亚)
	GreekAncient = "grc"  # (to 1453)(希腊语，古（到1453年）)
	Gujarati = "guj"  # (古吉拉特语)
	Haitian = "hat"  # Haitian;Haitian Creole(海天;海地克里奥尔语)
	Hebrew = "heb"  # (希伯来语)
	Hindi = "hin"  # (印地文)
	Croatian = "hrv"  # (克罗地亚)
	Hungarian = "hun"  # (匈牙利)
	Inuktitut = "iku"  # (因纽特语)
	Indonesian = "ind"  # (印尼)
	Icelandic = "isl"  # (冰岛)
	Italian = "ita"  # (意大利语)
	ItalianOld = "ita_old"  # Italian - Old(意大利语 - 旧)
	Javanese = "jav"  # (爪哇)
	Japanese = "jpn"  # (日本)
	Kannada = "kan"  # (卡纳达语)
	Georgian = "kat"  # (格鲁吉亚)
	GeorgianOld = "kat_old"  # 	Georgian - Old(格鲁吉亚 - 旧)
	Kazakh = "kaz"  # (哈萨克斯坦)
	CentralKhmer = "khm"  # (中央高棉)
	Kirghiz = "kir"  # Kirghiz;Kyrgyz(柯尔克孜;吉尔吉斯)
	Korean = "kor"  # (韩国)
	Kurdish = "kur"  # (库尔德人)
	Lao = "lao"  # (老挝)
	Latin = "lat"  # (拉丁)
	Latvian = "lav"  # (拉脱维亚)
	Lithuanian = "lit"  # (立陶宛)
	Malayalam = "mal"  # (马拉雅拉姆语)
	Marathi = "mar"  # (马拉)
	Macedonian = "mkd"  # (马其顿)
	Maltese = "mlt"  # (马耳他)
	Malay = "msa"  # (马来文)
	Burmese = "mya"  # (缅甸)
	Nepali = "nep"  # (尼泊尔)
	Dutch = "nld"  # Dutch;Flemish(荷兰;佛兰芒语)
	Norwegian = "nor"  # (挪威)
	Oriya = "ori"  # (奥里亚语)
	Orientation = "osd"  # Orientation and script detection module(定位及脚本检测模块)
	Panjabi = "pan"  # Panjabi;Punjabi(旁遮普语;旁遮普语)
	Polish = "pol"  # (波兰)
	Portuguese = "por"  # (葡萄牙语)
	Pushto = "pus"  # Pushto;Pashto(普什图语;普什图语)
	Romanian = "ron"  # Romanian;Moldavian;Moldovan(罗马尼亚;摩尔多瓦;摩尔多瓦)
	Russian = "rus"  # (俄罗斯)
	Sanskrit = "san"  # (梵文)
	Sinhala = "sin"  # Sinhala;Sinhalese(僧伽罗语;僧伽罗语)
	Slovak = "slk"  # (斯洛伐克)
	SlovakFraktur = "slk_frak"  # Slovak - Fraktur(斯洛伐克 - Fraktur)
	Slovenian = "slv"  # (斯洛文尼亚)
	Spanish = "spa"  # Spanish;Castilian(西班牙语;卡斯蒂利亚)
	SpanishOld = "spa_old"  # Spanish;Castilian - Old(西班牙语;卡斯蒂利亚 - 老)
	Albanian = "sqi"  # (阿尔巴尼亚)
	Serbian = "srp"  # (塞尔维亚)
	SerbianLatin = "srp_latn"  # Serbian - Latin(塞尔维亚语 - 拉丁语)
	Swahili = "swa"  # (斯瓦希里语)
	Swedish = "swe"  # (瑞典)
	Syriac = "syr"  # (叙利亚)
	Tamil = "tam"  # (泰米尔)
	Telugu = "tel"  # (泰卢固语)
	Tajik = "tgk"  # (塔吉克斯坦)
	Tagalog = "tgl"  # (菲律宾语)
	Thai = "tha"  # (泰国)
	Tigrinya = "tir"  # (提格雷语)
	Turkish = "tur"  # (土耳其)
	Uighur = "uig"  # Uighur;Uyghur(维吾尔族;维吾尔)
	Ukrainian = "ukr"  # (乌克兰)
	Urdu = "urd"  # (乌尔都语)
	Uzbek = "uzb"  # (乌兹别克斯坦)
	UzbekCyrilic = "uzb_cyrl"  # Uzbek - Cyrilic(乌兹别克斯坦 - Cyrilic)
	Vietnamese = "vie"  # (越南语)
	Yiddish = "yid"  # (意第绪语)

	def __add__(self, other):
		return f"{self.value}+{other.value}"

	def __radd__(self, other):
		return f"{other}+{self.value}"


if __name__ == "__main__":
	print([str(x.value) for x in Lang._member_map_.values()])
	print(Lang.Chinese + Lang.English + Lang.Afrikaans + Lang.Assamese)
	print(type(Lang.Chinese))
	print(getattr(BaiDuLang, Lang.Chinese.name))
