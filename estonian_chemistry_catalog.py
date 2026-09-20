"""Estonian Grade 8 chemistry curriculum, content and deterministic item bank.

The canonical learner content is Estonian.  English is a support translation.
The twelve-unit prelude assumes no chemical-symbol or calculation knowledge;
the following 35 units map to the 70-period Grade 8 reference sequence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import sqlalchemy as sa


COURSE_SLUG = "ee-grade-8-chemistry"
PROGRAM_CODE = "EE-PROK-2026-CHEM-G8"
FRAMEWORK_CODE = "EE-PROK"
CURRICULUM_VERSION = "2026-09-01"
SOURCE_URLS = [
    {"role": "canonical", "url": "https://www.riigiteataja.ee/akt/123122025007"},
    {"role": "canonical_appendix", "url": "https://www.riigiteataja.ee/aktilisa/1140/7202/0024/1m%20lisa4.pdf"},
    {"role": "supporting_2023", "url": "https://www.riigiteataja.ee/aktilisa/1080/3202/3005/18m_pohi_lisa4.pdf"},
    {"role": "english_translation_2023", "url": "https://www.riigiteataja.ee/tolkelisa/5290/4202/4002/4.pdf"},
    {"role": "grade_8_structure", "url": "https://oppekava.edu.ee/a/Keemia_v1"},
    {"role": "reference_pacing", "url": "https://oppekava.ee/wp-content/uploads/2015/07/Keemia_t%C3%B6%C3%B6kava_8_klass.pdf"},
]


TOPICS = [
    ("PRE", "Keemia eelkursus", "Chemistry prelude", 0,
     "Nullteadmistega alustaja ohutus-, sümboli- ja arvutusvalmidus.",
     "Safety, notation and calculation readiness for a zero-knowledge learner."),
    ("CHEM", "Millega tegeleb keemia?", "What chemistry involves", 12,
     "Ained, omadused, reaktsioonid, lahused, pihused ja massiprotsent.",
     "Substances, properties, reactions, solutions, dispersions and mass percentage."),
    ("ATOM", "Aatomiehitus ja ainete ehitus", "Atomic structure and composition", 14,
     "Aatom, perioodilisustabel, sümbolid, ioonid ning keemilised sidemed.",
     "Atoms, the periodic table, symbols, ions and chemical bonding."),
    ("OX", "Hapnik, vesinik ja oksiidid", "Oxygen, hydrogen and oxides", 16,
     "Gaaside omadused, põlemine, oksüdatsiooniaste, oksiidid ja võrrandid.",
     "Gas properties, combustion, oxidation states, oxides and equations."),
    ("ACID", "Happed ja alused", "Acids and bases", 12,
     "Happed, hüdroksiidid, soolad, pH, indikaatorid ja neutralisatsioon.",
     "Acids, hydroxides, salts, pH, indicators and neutralisation."),
    ("METAL", "Tuntumaid metalle", "Common metals", 16,
     "Metallide omadused, aktiivsus, redoks, kasutus ja korrosioon.",
     "Metal properties, activity, redox, uses and corrosion."),
]


OUTCOMES = [
    ("PRE", "PRE-01", "Eristab eset, materjali ja ainet ning toob argielulisi näiteid."),
    ("PRE", "PRE-02", "Tõlgendab põhilisi ohupiktogramme ja valib ohutu tegevuse."),
    ("PRE", "PRE-03", "Tunneb põhilisi laborivahendeid ja nende otstarvet."),
    ("PRE", "PRE-04", "Eristab vaatlust, mõõtmist, järeldust ja seletust."),
    ("PRE", "PRE-05", "Kasutab osakese, aatomi, elemendi ja molekuli algmõisteid."),
    ("PRE", "PRE-06", "Mõistab, et elemendi sümbol on kokkuleppeline lühend, mitte valmis teadmine."),
    ("PRE", "PRE-07", "Loeb keemilise valemi tähti ja alaindekseid."),
    ("PRE", "PRE-08", "Eristab valemi alaindeksit ja reaktsioonivõrrandi kordajat."),
    ("PRE", "PRE-09", "Kasutab massi- ja ruumalaühikuid ning teeb lihtsaid teisendusi."),
    ("PRE", "PRE-10", "Rakendab osa, terviku, suhte ja murru mõistet."),
    ("PRE", "PRE-11", "Arvutab protsendi sammhaaval koos ühikute ja mõistlikkuse kontrolliga."),
    ("PRE", "PRE-12", "Näitab valmisolekut alustada Grade 8 keemiakursust."),
    ("CHEM", "CHEM-01", "Võrdleb ja liigitab aineid füüsikaliste omaduste põhjal."),
    ("CHEM", "CHEM-02", "Eristab füüsikalist muutust ja keemilist reaktsiooni ning tunneb reaktsiooni tunnuseid."),
    ("CHEM", "CHEM-03", "Selgitab keemilise reaktsiooni esilekutsumise ja kiiruse mõjutamise võimalusi."),
    ("CHEM", "CHEM-04", "Järgib laboris ja argielus kemikaalidega töötamise ohutusnõudeid."),
    ("CHEM", "CHEM-05", "Eristab lahuseid ja pihuseid ning nende alaliike."),
    ("CHEM", "CHEM-06", "Lahendab lahuse massiprotsendi ülesandeid ja põhjendab lahenduskäiku."),
    ("ATOM", "ATOM-01", "Selgitab aatomi ehitust prootonite, neutronite ja elektronide abil."),
    ("ATOM", "ATOM-02", "Seostab umbes 25 olulise elemendi eestikeelse nimetuse ja sümboli."),
    ("ATOM", "ATOM-03", "Seostab perioodi ja A-rühma aatomi elektronstruktuuriga."),
    ("ATOM", "ATOM-04", "Koostab 1.–4. perioodi A-rühma elemendi elektronskeemi."),
    ("ATOM", "ATOM-05", "Eristab metallilisi ja mittemetallilisi elemente ning väärisgaase."),
    ("ATOM", "ATOM-06", "Eristab lihtainet ja liitainet ning loeb aine koostist valemist."),
    ("ATOM", "ATOM-07", "Eristab iooni neutraalsest aatomist ja selgitab iooni laengut."),
    ("ATOM", "ATOM-08", "Eristab kovalentset, ioonilist ja metallilist sidet eakohasel tasemel."),
    ("OX", "OX-01", "Selgitab hapniku rolli põlemises ja eluslooduses."),
    ("OX", "OX-02", "Selgitab osoonikihi tähtsust ja saastamise mõju."),
    ("OX", "OX-03", "Võrdleb hapniku ja vesiniku põhilisi omadusi."),
    ("OX", "OX-04", "Valib gaasi kogumise viisi tiheduse ja vees lahustuvuse järgi."),
    ("OX", "OX-05", "Määrab lihtsas valemis elementide oksüdatsiooniastmed."),
    ("OX", "OX-06", "Koostab oksiidi valemi nimetusest ja nimetuse valemist."),
    ("OX", "OX-07", "Koostab lihtaine ja hapniku ühinemisreaktsiooni võrrandi."),
    ("OX", "OX-08", "Tasakaalustab lihtsa reaktsioonivõrrandi aatomite jäävuse põhjal."),
    ("ACID", "ACID-01", "Tunneb valemi järgi ära happe, hüdroksiidi ja soola."),
    ("ACID", "ACID-02", "Seostab tähtsamate hapete ja happeanioonide nimetused ning valemid."),
    ("ACID", "ACID-03", "Koostab lihtsa hüdroksiidi või soola valemi nimetuse põhjal."),
    ("ACID", "ACID-04", "Hindab lahuse keskkonda pH ja indikaatori värvuse järgi."),
    ("ACID", "ACID-05", "Rakendab tugevate hapete ja leeliste ohutusnõudeid."),
    ("ACID", "ACID-06", "Selgitab hapete, aluste ja soolade kasutust igapäevaelus."),
    ("ACID", "ACID-07", "Selgitab neutralisatsiooni kui happe ja aluse vastastikust reaktsiooni."),
    ("ACID", "ACID-08", "Koostab ja tasakaalustab lihtsa neutralisatsioonivõrrandi."),
    ("METAL", "METAL-01", "Seostab metallide omadused metallilise sidemega."),
    ("METAL", "METAL-02", "Liigitab metalle pingerea abil aktiivsuse järgi."),
    ("METAL", "METAL-03", "Ennustab metalli ja happelahuse reaktsiooni kvalitatiivselt."),
    ("METAL", "METAL-04", "Selgitab temperatuuri ja peenestatuse mõju reaktsioonikiirusele."),
    ("METAL", "METAL-05", "Koostab metalli ja hapniku või happelahuse lihtsa reaktsioonivõrrandi."),
    ("METAL", "METAL-06", "Seostab redoksreaktsiooni oksüdatsiooniastmete muutusega."),
    ("METAL", "METAL-07", "Põhjendab raua, alumiiniumi, vase ja sulamite kasutust omadustega."),
    ("METAL", "METAL-08", "Selgitab roostetamist, seda soodustavaid tegureid ja korrosioonitõrjet."),
]


@dataclass(frozen=True)
class Unit:
    code: str
    topic: str
    title_et: str
    title_en: str
    outcome: str
    key_et: str
    key_en: str
    misconception_et: str
    misconception_en: str
    kind: str = "multiple_choice"
    periods: int = 2


def _u(code, topic, et, en, outcome, key_et, key_en, wrong_et, wrong_en, kind="multiple_choice", periods=2):
    return Unit(code, topic, et, en, outcome, key_et, key_en, wrong_et, wrong_en, kind, periods)


PRELUDE_UNITS = [
    _u("P01", "PRE", "Ese, materjal ja aine", "Object, material and substance", "PRE-01", "Aine on materjali keemiline koostisosa; üks ese võib koosneda mitmest ainest.", "A substance is a chemical constituent of a material; one object may contain several substances.", "Ese ja aine tähendavad alati sama asja.", "An object and a substance always mean the same thing."),
    _u("P02", "PRE", "Ohumärgid ja ohutu valik", "Hazard symbols and safe choices", "PRE-02", "Ohupiktogramm hoiatab kindla ohu eest ning juhib kaitsemeetme valikut.", "A hazard pictogram warns of a specific hazard and guides the protective action.", "Tundmatu kemikaali nuusutamine on ohutu viis selle määramiseks.", "Smelling an unknown chemical is a safe identification method."),
    _u("P03", "PRE", "Laborivahendite ABC", "Essential laboratory equipment", "PRE-03", "Mõõtesilinder sobib vedeliku ruumala mõõtmiseks; keeduklaas ei ole täppismõõteriist.", "A measuring cylinder measures liquid volume; a beaker is not a precision instrument.", "Kõiki anumaid kasutatakse sama otstarbega.", "All vessels are used for the same purpose."),
    _u("P04", "PRE", "Vaatlusest järelduseni", "From observation to conclusion", "PRE-04", "Vaatlus kirjeldab märgatut; järeldus seob tõendid uurimisküsimusega.", "An observation describes what was detected; a conclusion links evidence to the question.", "Järeldus on sama mis mõõdetud arv.", "A conclusion is the same as a measured number."),
    _u("P05", "PRE", "Osakesed, aatomid ja molekulid", "Particles, atoms and molecules", "PRE-05", "Element koosneb sama prootonite arvuga aatomitest; molekul koosneb seotud aatomitest.", "An element consists of atoms with the same proton number; a molecule contains bonded atoms.", "Iga aineosake on nähtav palja silmaga.", "Every particle of matter is visible to the naked eye."),
    _u("P06", "PRE", "Elemendi nimi ja sümbol", "Element names and symbols", "PRE-06", "Keemiline sümbol algab suure tähega ja võimalik teine täht on väike, näiteks Na.", "A chemical symbol starts with a capital and any second letter is lowercase, for example Na.", "Sümboli mõlemad tähed kirjutatakse suurelt.", "Both letters of a symbol are uppercase.", "short_answer"),
    _u("P07", "PRE", "Kuidas lugeda valemit", "How to read a formula", "PRE-07", "Valemis H₂O näitab alaindeks 2 kahte vesinikuaatomit; hapniku järel puuduv arv tähendab ühte.", "In H₂O the subscript 2 means two hydrogen atoms; no number after oxygen means one.", "Alaindeks näitab molekulide arvu klassiruumis.", "A subscript shows how many molecules are in the classroom.", "formula_builder"),
    _u("P08", "PRE", "Alaindeks ja kordaja", "Subscripts and coefficients", "PRE-08", "Kordaja 2 valemi ees tähendab kahte osakest; alaindeks kuulub aine valemi sisse.", "A coefficient 2 before a formula means two particles; a subscript belongs inside the formula.", "Tasakaalustamisel muudetakse aine alaindekseid.", "Balancing changes a substance's subscripts."),
    _u("P09", "PRE", "Mass, ruumala ja ühikud", "Mass, volume and units", "PRE-09", "1000 milligrammi on 1 gramm ja 1000 milliliitrit on 1 liiter.", "1000 milligrams equal 1 gram and 1000 millilitres equal 1 litre.", "100 milligrammi on 1 gramm.", "100 milligrams equal 1 gram.", "numeric_calculation"),
    _u("P10", "PRE", "Osa, tervik ja suhe", "Part, whole and ratio", "PRE-10", "Osa suhe tervikusse leitakse jagades osa tervikuga.", "The fraction of a whole is found by dividing the part by the whole.", "Osa suhe tervikusse leitakse arvud liites.", "The fraction of a whole is found by adding the numbers.", "numeric_calculation"),
    _u("P11", "PRE", "Protsent sammhaaval", "Percentages step by step", "PRE-11", "Protsent = osa ÷ tervik × 100%; vastusel peab olema protsendimärk.", "Percentage = part ÷ whole × 100%; the answer needs a percent sign.", "Protsendi leidmiseks jagatakse tervik osaga.", "To find a percentage, divide the whole by the part.", "numeric_calculation"),
    _u("P12", "PRE", "Valmis keemiat õppima", "Ready to learn chemistry", "PRE-12", "Valmis õppija loeb sümbolit ja alaindeksit, kasutab ühikuid ning valib ohutu tegevuse.", "A ready learner reads symbols and subscripts, uses units and chooses safe actions.", "Keemia alustamiseks tuleb kõik elemendid peast teada.", "Starting chemistry requires memorising every element."),
]


FORMAL_UNITS = [
    _u("C01", "CHEM", "Ainete füüsikalised omadused", "Physical properties of substances", "CHEM-01", "Sulamis- ja keemistemperatuur, tihedus, kõvadus, juhtivus ning värvus on füüsikalised omadused.", "Melting point, boiling point, density, hardness, conductivity and colour are physical properties.", "Värvus tõestab alati aine keemilise koostise.", "Colour always proves chemical composition."),
    _u("C02", "CHEM", "Tihedus ja mõõtmine", "Density and measurement", "CHEM-01", "Tihedus leitakse massi jagamisel ruumalaga ning esitatakse koos ühikuga.", "Density is mass divided by volume and is reported with a unit.", "Tihedus leitakse massi ja ruumala liitmisel.", "Density is found by adding mass and volume.", "numeric_calculation"),
    _u("C03", "CHEM", "Füüsikaline ja keemiline muutus", "Physical and chemical change", "CHEM-02", "Keemilises reaktsioonis tekivad uued ained; olekumuutus üksi on füüsikaline muutus.", "A chemical reaction forms new substances; a change of state alone is physical.", "Sulamine tekitab alati uue aine.", "Melting always creates a new substance."),
    _u("C04", "CHEM", "Reaktsiooni tunnused ja kiirus", "Reaction evidence and rate", "CHEM-03", "Gaasi teke, sade, püsiv värvuse muutus või energia muutus võib olla reaktsiooni tõend; tingimusi tuleb kontrollida.", "Gas formation, a precipitate, persistent colour change or energy change can be evidence of reaction; conditions must be controlled.", "Iga temperatuurimuutus tõestab üksinda reaktsiooni.", "Any temperature change alone proves a reaction."),
    _u("C05", "CHEM", "Lahused ja pihused", "Solutions and dispersions", "CHEM-05", "Lahus on ühtlane segu; suspensioonis või emulsioonis on hajunud osakesed või tilgad.", "A solution is uniform; a suspension or emulsion contains dispersed particles or droplets.", "Õli ja vee segu on tõeline lahus.", "Oil mixed with water is a true solution."),
    _u("C06", "CHEM", "Lahuse massiprotsent", "Mass percentage of a solution", "CHEM-06", "Massiprotsent = lahustunud aine mass ÷ lahuse kogumass × 100%.", "Mass percentage = solute mass ÷ total solution mass × 100%.", "Massiprotsent = lahusti mass ÷ lahustunud aine mass.", "Mass percentage = solvent mass ÷ solute mass.", "numeric_calculation"),
    _u("A01", "ATOM", "Aatomi ehitus", "Structure of the atom", "ATOM-01", "Prootonid ja neutronid asuvad tuumas, elektronid elektronkihtides; neutraalses aatomis on prootoneid ja elektrone võrdselt.", "Protons and neutrons are in the nucleus and electrons in shells; a neutral atom has equal protons and electrons.", "Elektronid paiknevad aatomituumas.", "Electrons are located in the nucleus.", "atom_builder"),
    _u("A02", "ATOM", "Elemendid H-st Ca-ni", "Elements from H to Ca", "ATOM-02", "Elemendi sümbol on kindel: näiteks H on vesinik, O hapnik, Na naatrium ja Cl kloor.", "Each element has a fixed symbol: H is hydrogen, O oxygen, Na sodium and Cl chlorine.", "Na on lämmastiku sümbol.", "Na is the symbol for nitrogen.", "short_answer"),
    _u("A03", "ATOM", "Olulised metallid ja mittemetallid", "Important metals and non-metals", "ATOM-02", "Fe on raud, Cu vask, Zn tsink, Ag hõbe, Au kuld ja Hg elavhõbe.", "Fe is iron, Cu copper, Zn zinc, Ag silver, Au gold and Hg mercury.", "Cu on kaltsiumi sümbol.", "Cu is the symbol for calcium."),
    _u("A04", "ATOM", "Perioodid ja rühmad", "Periods and groups", "ATOM-03", "Periood näitab hõivatud elektronkihtide arvu ja A-rühm väliskihi elektronide arvu.", "The period shows occupied electron shells and an A-group shows outer-shell electrons.", "Periood näitab neutronite arvu.", "The period shows the number of neutrons."),
    _u("A05", "ATOM", "Elektronskeemid", "Electron-shell diagrams", "ATOM-04", "Aatomnumber annab prootonite arvu ja neutraalsel aatomil ka elektronide arvu, mis jaotatakse kihtidesse.", "Atomic number gives proton count and, for a neutral atom, electron count to distribute into shells.", "Massiarv annab alati väliskihi elektronide arvu.", "Mass number always gives outer-shell electrons.", "atom_builder"),
    _u("A06", "ATOM", "Metall, mittemetall või väärisgaas", "Metal, non-metal or noble gas", "ATOM-05", "Metallilised elemendid paiknevad peamiselt tabeli vasakul, mittemetallid paremal ja väärisgaasid viimases rühmas.", "Metallic elements are mainly left in the table, non-metals right, and noble gases in the final group.", "Kõik perioodilisustabeli parempoolsed elemendid on metallid.", "All elements on the right of the periodic table are metals."),
    _u("A07", "ATOM", "Lihtaine, liitaine, ioon ja side", "Elements, compounds, ions and bonds", "ATOM-06", "Lihtaine sisaldab ühe elemendi aatomeid; liitaine vähemalt kahe elemendi aatomeid ning ioonil on elektrilaeng.", "An elemental substance contains one element; a compound contains at least two, and an ion carries charge.", "Ioon on alati elektriliselt neutraalne.", "An ion is always electrically neutral."),
    _u("O01", "OX", "Hapnik põlemises ja eluslooduses", "Oxygen in combustion and life", "OX-01", "Hapnik toetab põlemist ja on vajalik aeroobseks hingamiseks, kuid ise ei ole kütus.", "Oxygen supports combustion and aerobic respiration but is not itself a fuel.", "Hapnik põleb alati ise kütusena.", "Oxygen always burns as a fuel."),
    _u("O02", "OX", "Osoonikiht", "The ozone layer", "OX-02", "Stratosfääri osoon neelab kahjulikku ultraviolettkiirgust; osoonikihi hõrenemine suurendab UV-riski.", "Stratospheric ozone absorbs harmful ultraviolet radiation; depletion increases UV risk.", "Osoonikihi hõrenemine vähendab Maale jõudvat UV-kiirgust.", "Ozone depletion reduces UV reaching Earth."),
    _u("O03", "OX", "Hapniku omadused ja tõestamine", "Oxygen properties and test", "OX-03", "Hapnik on tavatingimustel värvitu gaas ja hõõguv pird süttib hapnikus uuesti.", "Oxygen is a colourless gas under ordinary conditions and relights a glowing splint.", "Hapnik kustutab hõõguva pirru ning see tõestab hapnikku.", "Oxygen extinguishes a glowing splint and that proves oxygen."),
    _u("O04", "OX", "Vesinik ja gaaside kogumine", "Hydrogen and gas collection", "OX-04", "Vesinik on õhust väiksema tihedusega ja vees halvasti lahustuv; kogumisviis valitakse nende omaduste järgi.", "Hydrogen is less dense than air and poorly soluble in water; collection follows those properties.", "Kõiki gaase kogutakse alati samal viisil.", "Every gas is always collected in the same way."),
    _u("O05", "OX", "Oksüdatsiooniaste", "Oxidation state", "OX-05", "Neutraalse ühendi oksüdatsiooniastmete summa on null; hapnik on tavaliselt −II.", "Oxidation states sum to zero in a neutral compound; oxygen is usually −II.", "Neutraalse ühendi oksüdatsiooniastmete summa on alati +1.", "Oxidation states in a neutral compound always sum to +1."),
    _u("O06", "OX", "Oksiidide valemid ja nimetused", "Oxide formulae and names", "OX-06", "Oksiid on hapniku ja teise elemendi ühend; valem peab andma elektriliselt tasakaalus koostise.", "An oxide is oxygen combined with another element; its formula must give a balanced composition.", "Iga hapnikku sisaldav aine on oksiid.", "Every oxygen-containing substance is an oxide.", "formula_builder"),
    _u("O07", "OX", "Ühinemisreaktsioonid hapnikuga", "Combination reactions with oxygen", "OX-07", "Lihtaine reageerimisel hapnikuga tekib vastav oksiid ja valemite ette pannakse tasakaalustavad kordajad.", "A simple substance reacting with oxygen forms its oxide and coefficients balance the equation.", "Tasakaalustamiseks muudetakse oksiidi valemit.", "The oxide formula is changed to balance the equation.", "equation_balance"),
    _u("O08", "OX", "Võrrandi tasakaalustamine", "Balancing equations", "OX-08", "Tasakaalustatud võrrandis on iga elemendi aatomeid võrrandi mõlemal poolel võrdselt.", "A balanced equation has equal numbers of every element's atoms on both sides.", "Tasakaalustatud võrrandis peab molekulide koguarv olema mõlemal poolel sama.", "A balanced equation must have the same total number of molecules on each side.", "equation_balance"),
    _u("H01", "ACID", "Hape, hüdroksiid või sool", "Acid, hydroxide or salt", "ACID-01", "Happe valem algab tavaliselt H-ga, hüdroksiid sisaldab OH-rühma ja sool koosneb katioonist ning happeanioonist.", "An acid formula usually starts with H, a hydroxide contains OH, and a salt contains a cation and acid anion.", "Kõik H-tähte sisaldavad ained on happed.", "Every substance containing H is an acid."),
    _u("H02", "ACID", "Tähtsamad happed ja anioonid", "Common acids and anions", "ACID-02", "HCl on vesinikkloriidhape ja annab kloriidiooni; H₂SO₄ on väävelhape ja annab sulfaatiooni.", "HCl is hydrochloric acid and gives chloride; H₂SO₄ is sulfuric acid and gives sulfate.", "HCl on hüdroksiid.", "HCl is a hydroxide."),
    _u("H03", "ACID", "Hüdroksiidide ja soolade valemid", "Hydroxide and salt formulae", "ACID-03", "Ioonide laengud peavad ühendi valemis tasakaalustuma, näiteks Na⁺ ja OH⁻ annavad NaOH.", "Ion charges must balance in a formula, for example Na⁺ and OH⁻ give NaOH.", "Ühendi valemis võib kogulaeng olla suvaline.", "A compound formula may have any total charge.", "formula_builder"),
    _u("H04", "ACID", "pH ja indikaatorid", "pH and indicators", "ACID-04", "pH alla 7 on happeline, 7 neutraalne ja üle 7 aluseline; indikaatori värv annab keskkonna kohta tõendi.", "pH below 7 is acidic, 7 neutral and above 7 alkaline; indicator colour provides evidence.", "pH 2 lahus on aluseline.", "A solution at pH 2 is alkaline."),
    _u("H05", "ACID", "Hapete, leeliste ja soolade ohutu kasutus", "Safe use of acids, alkalis and salts", "ACID-05", "Tugeva happe või leelise korral kasutatakse kaitsevahendeid ning pritsmed loputatakse kohe rohke veega. Aine argikasutus ei muuda ohtlikku kemikaali ohutuks.", "Strong acids and alkalis require protection, and splashes are rinsed immediately with plenty of water. Everyday use does not make a hazardous chemical safe.", "Happepritsmeid neutraliseeritakse nahal teise söövitava ainega.", "Acid splashes on skin are neutralised with another corrosive chemical."),
    _u("H07", "ACID", "Neutralisatsioon ja võrrand", "Neutralisation and equations", "ACID-08", "Happe ja aluse neutralisatsioonil tekivad sool ja vesi ning võrrand tasakaalustatakse kordajatega.", "Acid-base neutralisation forms salt and water and is balanced with coefficients.", "Neutralisatsioonil tekib alati ainult vesinikgaas.", "Neutralisation always produces only hydrogen gas.", "equation_balance"),
    _u("M01", "METAL", "Metallide omadused ja side", "Metal properties and bonding", "METAL-01", "Metallide elektri- ja soojusjuhtivus, läige ning plastilisus seostuvad metallilise sideme ja liikuvate elektronidega.", "Metal conductivity, lustre and malleability relate to metallic bonding and mobile electrons.", "Metallid on alati haprad ega juhi elektrit.", "Metals are always brittle and do not conduct electricity."),
    _u("M02", "METAL", "Metallide pingerida", "Metal activity series", "METAL-02", "Pingerida võimaldab võrrelda metallide reaktsioonivõimet: aktiivsem metall paikneb kõrgemal.", "The activity series compares reactivity: a more active metal is placed higher.", "Pingerida järjestab metallid ainult tiheduse järgi.", "The activity series orders metals only by density."),
    _u("M03", "METAL", "Metall ja happelahus", "Metal and acid", "METAL-03", "Vesinikust aktiivsem sobiv metall võib lahja happega anda soola ja vesiniku; vask tavaliselt lahja HCl-ga ei reageeri.", "A suitable metal above hydrogen can form salt and hydrogen with dilute acid; copper normally does not react with dilute HCl.", "Kõik metallid reageerivad lahja HCl-ga ühesuguse kiirusega.", "All metals react with dilute HCl at the same rate."),
    _u("M04", "METAL", "Reaktsioonikiiruse võrdlemine", "Comparing reaction rates", "METAL-04", "Kõrgem temperatuur ja suurem pindala võivad osakeste tõhusate põrgete sagedust suurendada.", "Higher temperature and greater surface area can increase the frequency of successful particle collisions.", "Suurem metallitükk reageerib alati kiiremini, sest selle pindala ruumala kohta on väiksem.", "A larger metal lump always reacts faster because its surface-area-to-volume ratio is lower."),
    _u("M05", "METAL", "Metallide reaktsioonid hapnikuga", "Metals reacting with oxygen", "METAL-05", "Metalli reageerimisel hapnikuga tekib metallioksiid; võrrandis säilib iga elemendi aatomite arv.", "A metal reacting with oxygen forms a metal oxide; atom counts are conserved in the equation.", "Metall ja hapnik annavad alati happe.", "A metal and oxygen always form an acid.", "equation_balance"),
    _u("M06", "METAL", "Redoks oksüdatsiooniastmete kaudu", "Redox through oxidation states", "METAL-06", "Oksüdatsioonil oksüdatsiooniaste suureneb ja redutseerumisel väheneb; metall toimib sageli redutseerijana.", "Oxidation raises oxidation state and reduction lowers it; a metal often acts as the reducing agent.", "Oksüdatsioonil oksüdatsiooniaste alati väheneb.", "Oxidation always lowers oxidation state."),
    _u("M07", "METAL", "Raud, alumiinium, vask ja sulamid", "Iron, aluminium, copper and alloys", "METAL-07", "Materjal valitakse omaduste järgi: vask juhib hästi, alumiinium on kerge ja teras võib olla tugev.", "A material is selected by properties: copper conducts well, aluminium is light, and steel can be strong.", "Kõik metallid sobivad igaks otstarbeks võrdselt hästi.", "All metals suit every purpose equally well."),
    _u("M08", "METAL", "Roostemine ja korrosioonitõrje", "Rusting and corrosion protection", "METAL-08", "Raua roostemiseks on vaja vett ja hapnikku; värv, õli või kaitsekiht piirab nende juurdepääsu.", "Iron rusting requires water and oxygen; paint, oil or a protective coating limits their access.", "Raud roostetab kõige kiiremini täiesti kuivas hapnikuta keskkonnas.", "Iron rusts fastest in a completely dry oxygen-free environment."),
]

ALL_UNITS = PRELUDE_UNITS + FORMAL_UNITS

# H05 integrates safe handling with the official everyday-use outcome so the
# formal programme remains 35 substantial two-period units.
EXTRA_UNIT_OUTCOMES = {
    "C04": ("CHEM-04",),
    "A07": ("ATOM-07", "ATOM-08"),
    "H05": ("ACID-06",),
    "H07": ("ACID-07",),
}


def _content(unit: Unit, language: str) -> str:
    et = language == "et"
    title = unit.title_et if et else unit.title_en
    key = unit.key_et if et else unit.key_en
    misconception = unit.misconception_et if et else unit.misconception_en
    if et:
        return f"""# {title}

## Õpieesmärk

Alustame nullist ja liigume ühe kontrollitava sammu kaupa. Selle tunni siht on **{unit.outcome}**.

## Põhiidee

{key}

## Kuidas mõelda

1. Kirjuta välja, mida ülesandes antakse.
2. Nimeta sümbol, mõiste või ühik enne selle kasutamist.
3. Tee ainult üks põhjendatud samm korraga.
4. Kontrolli, kas vastus sobib ühikute, ohutuse ja argimõistusega.

## Levinud väärarusaam

„{misconception}” See ei ole õige. Võrdle väidet põhiideega ja otsi konkreetset tõendit.

## Enesekontroll

Selgita põhiidee oma sõnadega ning too üks ohutu argieluline või laboratoorne näide. Kui kasutad valemit, kirjuta iga sümboli tähendus välja.
"""
    return f"""# {title}

## Learning goal

We assume no prior chemical notation and move one checkable step at a time. This lesson targets **{unit.outcome}**.

## Key idea

{key}

## Reasoning routine

1. Write down what the task gives you.
2. Name every symbol, concept or unit before using it.
3. Make one justified step at a time.
4. Check the answer against units, safety and everyday reasonableness.

## Common misconception

“{misconception}” This is not correct. Compare it with the key idea and identify concrete evidence.

## Self-check

Explain the key idea in your own words and give one safe everyday or laboratory example. If you use a formula, state what every symbol means.
"""


def _question(unit: Unit, index: int, language: str) -> dict:
    et = language == "et"
    title = unit.title_et if et else unit.title_en
    correct = unit.key_et if et else unit.key_en
    misconception = unit.misconception_et if et else unit.misconception_en
    generic_wrong = ([
        "Ühikuid ja ohutusnõudeid ei ole keemias vaja kontrollida.",
        "Keemiline sümbol tähendab alati sama mis igapäevane sõna.",
    ] if et else [
        "Units and safety requirements never need checking in chemistry.",
        "A chemical symbol always means the same thing as an everyday word.",
    ])
    stems_et = [
        "Milline väide on teaduslikult õige?",
        "Milline märge sobib tunni „{title}” kokkuvõttesse?",
        "Õpilane kontrollib oma arusaamist. Milline väide tuleks alles jätta?",
        "Milline vastus kasutab Grade 8 keemia mõistet õigesti?",
        "Milline väide on kooskõlas õpitulemusega {outcome}?",
        "Milline seletus väldib selle teema levinud väärarusaama?",
        "Milline järeldus on tõenditega kõige paremini põhjendatud?",
        "Milline valik oleks ohutu ja keemiliselt korrektne?",
        "Milline väide sobib enne arvutuse või valemi kasutamist?",
        "Milline vastus sisaldab vajalikku mõistet ja põhjendust?",
        "Milline väide kuulub Eesti 8. klassi selle teema ulatusse?",
        "Milline vastus aitaks kaasõpilasel vea parandada?",
        "Milline kokkuvõte on täpne ilma Grade 9 teemadesse minemata?",
    ]
    stems_en = [
        "Which statement is scientifically correct?",
        "Which note belongs in a summary of “{title}”?",
        "A learner checks their understanding. Which statement should remain?",
        "Which answer uses the Grade 8 chemistry concept correctly?",
        "Which statement aligns with outcome {outcome}?",
        "Which explanation avoids the common misconception in this topic?",
        "Which conclusion is best supported by evidence?",
        "Which choice is both safe and chemically correct?",
        "Which statement belongs before using a calculation or formula?",
        "Which answer includes the necessary concept and reasoning?",
        "Which statement is within the Estonian Grade 8 scope for this topic?",
        "Which answer would help a classmate correct their mistake?",
        "Which summary is accurate without drifting into Grade 9 content?",
    ]
    stem = (stems_et if et else stems_en)[index % 13].format(title=title, outcome=unit.outcome)
    options = [correct, misconception, *generic_wrong]
    shift = index % len(options)
    options = options[shift:] + options[:shift]
    return {
        "question_text": f"{title}: {stem}",
        "options": options,
        "correct_answer": correct,
        "explanation": (f"Õige vastus seostub otseselt õpitulemusega {unit.outcome}: {correct}" if et else
                        f"The correct answer directly addresses outcome {unit.outcome}: {correct}"),
    }


def fixed_question_count() -> int:
    return len(PRELUDE_UNITS) * 5 + len(FORMAL_UNITS) * 13


def _exercise_payload(unit: Unit, language: str) -> tuple[dict, dict]:
    et = language == "et"
    q = _question(unit, 0, language)
    ui = {
        "check": "Kontrolli vastust" if et else "Check answer",
        "level": "Keemia eelkursus" if unit.topic == "PRE" and et else
                 "Chemistry prelude" if unit.topic == "PRE" else
                 "Eesti 8. klassi keemia" if et else "Estonian Grade 8 chemistry",
        "answer": "Vastus" if et else "Answer",
        "text_answer": "Kirjuta vastus" if et else "Type your answer",
        "coefficient": "Kordaja" if et else "Coefficient",
        "protons": "Prootonid" if et else "Protons",
        "neutrons": "Neutronid" if et else "Neutrons",
        "electrons": "Elektronid" if et else "Electrons",
    }
    public = {"choices": q["options"], "ui": ui}
    answer: dict = {"choice": q["options"].index(q["correct_answer"])}
    if unit.kind == "atom_builder":
        public = {"atom": "Na", "atomic_number": 11, "mass_number": 23, "ui": ui}
        answer = {"protons": 11, "neutrons": 12, "electrons": 11}
    elif unit.kind == "equation_balance":
        equations = {
            "H07": (["HCl", "NaOH", "NaCl", "H₂O"], ["+", "→", "+"], [1, 1, 1, 1]),
            "M05": (["Mg", "O₂", "MgO"], ["+", "→"], [2, 1, 2]),
        }
        terms, operators, coefficients = equations.get(unit.code, (["H₂", "O₂", "H₂O"], ["+", "→"], [2, 1, 2]))
        public = {"equation": terms, "operators": operators, "ui": ui}
        answer = {"coefficients": coefficients}
    elif unit.kind == "numeric_calculation":
        numeric = {
            "P09": ("20 000 mg = mitu grammi?" if et else "How many grams are 20,000 mg?", "g"),
            "P10": ("Mitu protsenti on 20 osa 100 osast?" if et else "What percentage is 20 parts out of 100?", "%"),
            "P11": ("10 g on 50 g tervikust. Mitu protsenti see on?" if et else "10 g is part of a 50 g whole. What percentage is it?", "%"),
            "C02": ("Proovi mass on 40 g ja ruumala 2 cm³. Leia tihedus." if et else "A sample has mass 40 g and volume 2 cm³. Find its density.", "g/cm³"),
            "C06": ("100 g lahuses on 20 g lahustunud ainet. Leia massiprotsent." if et else "A 100 g solution contains 20 g solute. Find the mass percentage.", "%"),
        }
        prompt, unit_label = numeric[unit.code]
        public = {"unit": unit_label, "prompt_override": prompt, "ui": ui, "worked_steps": ["Kirjuta antud suurused", "Vali seos", "Asenda arvud", "Lisa ühik"] if et else ["List the known values", "Choose the relationship", "Substitute", "Add the unit"]}
        answer = {"value": 20.0, "tolerance": 0.01}
    elif unit.kind == "formula_builder":
        formulae = {
            "P07": ("Kirjuta vee valem." if et else "Write the formula of water.", ["H2O", "H₂O"]),
            "O06": ("Kirjuta magneesiumoksiidi valem." if et else "Write the formula of magnesium oxide.", ["MgO"]),
            "H03": ("Kirjuta naatriumhüdroksiidi valem." if et else "Write the formula of sodium hydroxide.", ["NaOH"]),
        }
        prompt, accepted = formulae[unit.code]
        public = {"ui": ui, "placeholder": accepted[0], "prompt_override": prompt}
        if unit.code == "P07":
            public["molecule"] = "water"
        answer = {"text": accepted[0], "accepted": accepted, "case_sensitive": True}
    elif unit.kind == "short_answer":
        short_answers = {
            "P06": ("Kirjuta naatriumi keemiline sümbol." if et else "Write the chemical symbol for sodium.", ["Na"]),
            "A02": ("Kirjuta hapniku keemiline sümbol." if et else "Write the chemical symbol for oxygen.", ["O"]),
        }
        prompt, accepted = short_answers[unit.code]
        public = {"ui": ui, "placeholder": accepted[0], "prompt_override": prompt}
        answer = {"text": accepted[0], "accepted": accepted, "case_sensitive": True}
    correct_display = (answer.get("accepted") or [answer.get("value") or answer.get("coefficients") or q["correct_answer"]])[0]
    answer["feedback"] = {
        language: {"correct_answer": str(correct_display), "explanation": q["explanation"]}
    }
    return public, answer


def seed_curricula_and_estonian_chemistry(conn, schema: str) -> dict:
    """Seed country profiles and the Estonian zero-prerequisite Grade 8 model."""
    framework_id = conn.execute(sa.text(f"""
        INSERT INTO {schema}.curriculum_frameworks
            (country_code,jurisdiction_code,code,title,version,effective_from,
             authority,canonical_language,supported_languages,source_urls)
        VALUES ('EE','EE',:code,'Põhikooli riiklik õppekava',:version,'2026-09-01',
                'Eesti Vabariigi Valitsus','et',CAST('["et","en"]' AS jsonb),CAST(:sources AS jsonb))
        ON CONFLICT (code,version) DO UPDATE SET source_urls=EXCLUDED.source_urls,
            canonical_language='et',supported_languages=EXCLUDED.supported_languages
        RETURNING id
    """), {"code": FRAMEWORK_CODE, "version": CURRICULUM_VERSION,
            "sources": json.dumps(SOURCE_URLS)}).scalar_one()
    program_id = conn.execute(sa.text(f"""
        INSERT INTO {schema}.curriculum_programs
            (framework_id,code,subject_code,subject_title,stage_code,grade_code,
             estimated_periods,description,is_active)
        VALUES (:framework,:code,'chemistry','Keemia','III','8',70,
                'Eesti 8. klassi keemia: 35 üksust, 70 tundi ja nullteadmistega eelkursus.',true)
        ON CONFLICT (code) DO UPDATE SET framework_id=EXCLUDED.framework_id,
            estimated_periods=70,description=EXCLUDED.description,is_active=true
        RETURNING id
    """), {"framework": framework_id, "code": PROGRAM_CODE}).scalar_one()

    topic_ids = {}
    for order_idx, (code, title_et, _title_en, periods, desc_et, _desc_en) in enumerate(TOPICS):
        topic_ids[code] = conn.execute(sa.text(f"""
            INSERT INTO {schema}.curriculum_topics
                (program_id,code,title,description,order_idx,recommended_periods)
            VALUES (:program,:code,:title,:description,:order_idx,:periods)
            ON CONFLICT (program_id,code) DO UPDATE SET title=EXCLUDED.title,
                description=EXCLUDED.description,order_idx=EXCLUDED.order_idx,
                recommended_periods=EXCLUDED.recommended_periods
            RETURNING id
        """), {"program": program_id, "code": code, "title": title_et,
                "description": desc_et, "order_idx": order_idx, "periods": periods}).scalar_one()
    outcome_ids = {}
    for order_idx, (topic, code, description) in enumerate(OUTCOMES):
        excluded = ["moolarvutused", "anorgaaniliste ainete põhiklasside süsteem", "süsinikuühendid"] if topic != "PRE" else []
        stored_code = f"EE-PROK-CHEM-G8-{code}"
        outcome_ids[code] = conn.execute(sa.text(f"""
            INSERT INTO {schema}.curriculum_outcomes
                (topic_id,code,description,prerequisites,allowed_scope,excluded_scope,order_idx)
            VALUES (:topic,:code,:description,'[]'::jsonb,CAST(:allowed AS jsonb),CAST(:excluded AS jsonb),:order_idx)
            ON CONFLICT (code) DO UPDATE SET topic_id=EXCLUDED.topic_id,
                description=EXCLUDED.description,allowed_scope=EXCLUDED.allowed_scope,
                excluded_scope=EXCLUDED.excluded_scope,order_idx=EXCLUDED.order_idx
            RETURNING id
        """), {"topic": topic_ids[topic], "code": stored_code, "description": description,
                "allowed": json.dumps([description]), "excluded": json.dumps(excluded),
                "order_idx": order_idx}).scalar_one()

    # Register England separately so no existing course is relabelled as Estonian.
    england_framework = conn.execute(sa.text(f"""
        INSERT INTO {schema}.curriculum_frameworks
            (country_code,jurisdiction_code,code,title,version,authority,
             canonical_language,supported_languages,source_urls)
        VALUES ('GB','GB-ENG','GB-ENG-NC','England national curriculum','current',
                'Department for Education','en',CAST('["en","et"]' AS jsonb),'[]'::jsonb)
        ON CONFLICT (code,version) DO UPDATE SET jurisdiction_code='GB-ENG'
        RETURNING id
    """)).scalar_one()
    england_profiles = [
        ("GB-ENG-SCI-PRIMARY", "science", "Science", "KS1-KS2", "PRIMARY", "primary-science"),
        ("GB-ENG-CHEM-SECONDARY", "chemistry", "Chemistry", "KS3-KS4", "SECONDARY", "chemistry-fundamentals"),
        ("GB-ENG-CHEM-POST16", "chemistry", "Chemistry", "POST16", "POST-16", "advanced-chemistry"),
    ]
    for code, subject, title, stage, grade, slug in england_profiles:
        english_program = conn.execute(sa.text(f"""
            INSERT INTO {schema}.curriculum_programs
                (framework_id,code,subject_code,subject_title,stage_code,grade_code,description,is_active)
            VALUES (:framework,:code,:subject,:title,:stage,:grade,'England-aligned reference pathway.',true)
            ON CONFLICT (code) DO UPDATE SET framework_id=EXCLUDED.framework_id,is_active=true
            RETURNING id
        """), {"framework": england_framework, "code": code, "subject": subject,
                "title": title, "stage": stage, "grade": grade}).scalar_one()
        row = conn.execute(sa.text(f"SELECT id FROM {schema}.courses WHERE slug=:slug"), {"slug": slug}).scalar()
        if row:
            conn.execute(sa.text(f"""
                UPDATE {schema}.courses SET country_code='GB',jurisdiction_code='GB-ENG',
                    curriculum_code=:code,curriculum_version='current',grade_code=:grade,
                    canonical_language='en',supported_languages=CAST('["en","et"]' AS jsonb)
                WHERE id=:course
            """), {"code": code, "grade": grade, "course": row})
            conn.execute(sa.text(f"""
                INSERT INTO {schema}.course_curriculum_profiles (course_id,program_id)
                VALUES (:course,:program) ON CONFLICT (course_id) DO UPDATE SET program_id=EXCLUDED.program_id
            """), {"course": row, "program": english_program})

    course = conn.execute(sa.text(f"""
        INSERT INTO {schema}.courses
            (title,slug,description,category,difficulty,is_published,is_default,
             country_code,jurisdiction_code,curriculum_code,curriculum_version,
             grade_code,canonical_language,supported_languages)
        VALUES ('Eesti 8. klassi keemia',:slug,
                'Nullteadmistega eelkursus ja Eesti riikliku õppekava 35 üksust / 70 tundi.',
                'Keemia','intermediate',true,true,'EE','EE',:program,:version,'8','et',
                CAST('["et","en"]' AS jsonb))
        ON CONFLICT (slug) DO UPDATE SET title=EXCLUDED.title,description=EXCLUDED.description,
            category=EXCLUDED.category,difficulty=EXCLUDED.difficulty,is_published=true,is_default=true,
            country_code='EE',jurisdiction_code='EE',curriculum_code=:program,
            curriculum_version=:version,grade_code='8',canonical_language='et',
            supported_languages=EXCLUDED.supported_languages
        RETURNING *
    """), {"slug": COURSE_SLUG, "program": PROGRAM_CODE, "version": CURRICULUM_VERSION}).mappings().one()
    course_id = course["id"]
    conn.execute(sa.text(f"""
        INSERT INTO {schema}.course_curriculum_profiles (course_id,program_id)
        VALUES (:course,:program) ON CONFLICT (course_id) DO UPDATE SET program_id=EXCLUDED.program_id
    """), {"course": course_id, "program": program_id})
    conn.execute(sa.text(f"""
        INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title,description)
        VALUES ('courses',:id,'en','Estonian Grade 8 Chemistry',
                'A zero-knowledge prelude followed by the 35-unit, 70-period Estonian national Grade 8 pathway.')
        ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET
            title=EXCLUDED.title,description=EXCLUDED.description
    """), {"id": course_id})

    units_by_topic = {code: [] for code, *_ in TOPICS}
    for unit in ALL_UNITS:
        units_by_topic[unit.topic].append(unit)
    lesson_ids = {}
    previous_lesson_id = None
    for module_order, (topic_code, title_et, title_en, periods, desc_et, desc_en) in enumerate(TOPICS):
        module_id = conn.execute(sa.text(f"""
            SELECT id FROM {schema}.modules WHERE course_id=:course AND order_idx=:order_idx ORDER BY id LIMIT 1
        """), {"course": course_id, "order_idx": module_order}).scalar()
        if not module_id:
            module_id = conn.execute(sa.text(f"""
                INSERT INTO {schema}.modules (course_id,title,description,order_idx)
                VALUES (:course,:title,:description,:order_idx) RETURNING id
            """), {"course": course_id, "title": title_et, "description": desc_et,
                    "order_idx": module_order}).scalar_one()
        else:
            conn.execute(sa.text(f"UPDATE {schema}.modules SET title=:title,description=:description WHERE id=:id"),
                         {"title": title_et, "description": desc_et, "id": module_id})
        conn.execute(sa.text(f"""
            INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title,description)
            VALUES ('modules',:id,'en',:title,:description)
            ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title,description=EXCLUDED.description
        """), {"id": module_id, "title": title_en, "description": desc_en})
        for order_idx, unit in enumerate(units_by_topic[topic_code]):
            lesson_id = conn.execute(sa.text(f"""
                SELECT id FROM {schema}.lessons WHERE module_id=:module AND order_idx=:order_idx ORDER BY id LIMIT 1
            """), {"module": module_id, "order_idx": order_idx}).scalar()
            values = {"module": module_id, "title": unit.title_et, "content": _content(unit, "et"),
                      "duration": 20 if topic_code == "PRE" else 90, "order_idx": order_idx,
                      "kind": "prelude" if topic_code == "PRE" else "core", "prerequisite": previous_lesson_id}
            if lesson_id:
                conn.execute(sa.text(f"""
                    UPDATE {schema}.lessons SET title=:title,content_md=:content,duration_min=:duration,
                        order_idx=:order_idx,lesson_kind=:kind,prerequisite_lesson_id=:prerequisite WHERE id=:id
                """), {**values, "id": lesson_id})
            else:
                lesson_id = conn.execute(sa.text(f"""
                    INSERT INTO {schema}.lessons
                        (module_id,title,content_md,duration_min,xp_reward,order_idx,lesson_kind,difficulty_level,prerequisite_lesson_id)
                    VALUES (:module,:title,:content,:duration,25,:order_idx,:kind,1,:prerequisite) RETURNING id
                """), values).scalar_one()
            lesson_ids[unit.code] = lesson_id
            previous_lesson_id = lesson_id
            conn.execute(sa.text(f"""
                INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title,content_md)
                VALUES ('lessons',:id,'en',:title,:content)
                ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title,content_md=EXCLUDED.content_md
            """), {"id": lesson_id, "title": unit.title_en, "content": _content(unit, "en")})
            outcome_id = outcome_ids[unit.outcome]
            conn.execute(sa.text(f"""
                INSERT INTO {schema}.lesson_curriculum_outcomes (lesson_id,outcome_id)
                VALUES (:lesson,:outcome) ON CONFLICT DO NOTHING
            """), {"lesson": lesson_id, "outcome": outcome_id})
            for extra_outcome in EXTRA_UNIT_OUTCOMES.get(unit.code, ()):
                conn.execute(sa.text(f"""
                    INSERT INTO {schema}.lesson_curriculum_outcomes (lesson_id,outcome_id)
                    VALUES (:lesson,:outcome) ON CONFLICT DO NOTHING
                """), {"lesson": lesson_id, "outcome": outcome_ids[extra_outcome]})

            public_et, answer_et = _exercise_payload(unit, "et")
            public_en, answer_en = _exercise_payload(unit, "en")
            answer_et.setdefault("feedback", {})["en"] = answer_en["feedback"]["en"]
            source_key = f"ee-g8-{unit.code.lower()}"
            prompt_et = public_et.pop("prompt_override", _question(unit, 0, "et")["question_text"])
            prompt_en = public_en.pop("prompt_override", _question(unit, 0, "en")["question_text"])
            exercise_id = conn.execute(sa.text(f"""
                INSERT INTO {schema}.interactive_exercises
                    (source_key,engine,exercise_type,prompt,concepts,difficulty_band,cognitive_layer,public_payload,answer_payload)
                VALUES (:source,'chemistry',:kind,:prompt,CAST(:concepts AS jsonb),1,'skill',CAST(:public AS jsonb),CAST(:answer AS jsonb))
                ON CONFLICT (source_key) DO UPDATE SET exercise_type=EXCLUDED.exercise_type,prompt=EXCLUDED.prompt,
                    concepts=EXCLUDED.concepts,public_payload=EXCLUDED.public_payload,answer_payload=EXCLUDED.answer_payload
                RETURNING id
            """), {"source": source_key, "kind": unit.kind, "prompt": prompt_et,
                    "concepts": json.dumps([unit.outcome]), "public": json.dumps(public_et),
                    "answer": json.dumps(answer_et)}).scalar_one()
            conn.execute(sa.text(f"""
                INSERT INTO {schema}.exercise_translations (exercise_id,language,prompt,public_payload)
                VALUES (:exercise,'en',:prompt,CAST(:public AS jsonb))
                ON CONFLICT (exercise_id,language) DO UPDATE SET prompt=EXCLUDED.prompt,public_payload=EXCLUDED.public_payload
            """), {"exercise": exercise_id, "prompt": prompt_en,
                    "public": json.dumps(public_en)})
            conn.execute(sa.text(f"INSERT INTO {schema}.lesson_exercises (lesson_id,exercise_id,order_idx) VALUES (:lesson,:exercise,0) ON CONFLICT DO NOTHING"),
                         {"lesson": lesson_id, "exercise": exercise_id})
            conn.execute(sa.text(f"INSERT INTO {schema}.exercise_curriculum_outcomes (exercise_id,outcome_id) VALUES (:exercise,:outcome) ON CONFLICT DO NOTHING"),
                         {"exercise": exercise_id, "outcome": outcome_id})
            for extra_outcome in EXTRA_UNIT_OUTCOMES.get(unit.code, ()):
                conn.execute(sa.text(f"INSERT INTO {schema}.exercise_curriculum_outcomes (exercise_id,outcome_id) VALUES (:exercise,:outcome) ON CONFLICT DO NOTHING"),
                             {"exercise": exercise_id, "outcome": outcome_ids[extra_outcome]})

            quiz_id = conn.execute(sa.text(f"SELECT id FROM {schema}.quizzes WHERE lesson_id=:lesson ORDER BY id LIMIT 1"),
                                   {"lesson": lesson_id}).scalar()
            if not quiz_id:
                quiz_id = conn.execute(sa.text(f"""
                    INSERT INTO {schema}.quizzes (lesson_id,title,pass_threshold,xp_reward)
                    VALUES (:lesson,:title,70,30) RETURNING id
                """), {"lesson": lesson_id, "title": f"{unit.title_et} – kontroll"}).scalar_one()
            count = 5 if topic_code == "PRE" else 13
            for question_idx in range(count):
                et_q = _question(unit, question_idx, "et")
                en_q = _question(unit, question_idx, "en")
                reserved_order = 100 + question_idx
                question_id = conn.execute(sa.text(f"""
                    SELECT id FROM {schema}.quiz_questions WHERE quiz_id=:quiz AND order_idx=:order_idx ORDER BY id LIMIT 1
                """), {"quiz": quiz_id, "order_idx": reserved_order}).scalar()
                params = {"quiz": quiz_id, "text": et_q["question_text"], "options": json.dumps(et_q["options"]),
                          "answer": et_q["correct_answer"], "explanation": et_q["explanation"],
                          "order_idx": reserved_order, "difficulty": 1 + question_idx % 3,
                          "kind": ["single_choice", "classification", "data_interpretation", "safety_scenario", "reasoned_choice"][question_idx % 5],
                          "cognitive": ["remember", "understand", "apply", "analyse"][question_idx % 4],
                          "misconception": unit.misconception_et, "solution": unit.key_et,
                          "safety": "laboratory" if unit.outcome in {"PRE-02", "PRE-03", "CHEM-04", "ACID-05"} else "none",
                          "scope": f"Aligned to {unit.outcome}; Grade 9 mole, extended inorganic-class and carbon-compound content excluded."}
                if question_id:
                    conn.execute(sa.text(f"""
                        UPDATE {schema}.quiz_questions SET question_text=:text,options=CAST(:options AS jsonb),
                            correct_answer=:answer,explanation=:explanation,difficulty_level=:difficulty,
                            source_type='authored',question_kind=:kind,cognitive_process=:cognitive,
                            misconception_target=:misconception,worked_solution=:solution,
                            safety_classification=:safety,scope_confirmation=:scope WHERE id=:id
                    """), {**params, "id": question_id})
                else:
                    question_id = conn.execute(sa.text(f"""
                        INSERT INTO {schema}.quiz_questions
                            (quiz_id,question_text,options,correct_answer,explanation,order_idx,
                             difficulty_level,source_type,question_kind,cognitive_process,
                             misconception_target,worked_solution,safety_classification,scope_confirmation)
                        VALUES (:quiz,:text,CAST(:options AS jsonb),:answer,:explanation,:order_idx,
                                :difficulty,'authored',:kind,:cognitive,:misconception,:solution,:safety,:scope)
                        RETURNING id
                    """), params).scalar_one()
                conn.execute(sa.text(f"""
                    INSERT INTO {schema}.content_translations
                        (entity_type,entity_id,language,question_text,options,correct_answer,explanation)
                    VALUES ('quiz_questions',:id,'en',:text,CAST(:options AS jsonb),:answer,:explanation)
                    ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET question_text=EXCLUDED.question_text,
                        options=EXCLUDED.options,correct_answer=EXCLUDED.correct_answer,explanation=EXCLUDED.explanation
                """), {"id": question_id, "text": en_q["question_text"], "options": json.dumps(en_q["options"]),
                        "answer": en_q["correct_answer"], "explanation": en_q["explanation"]})
                conn.execute(sa.text(f"""
                    INSERT INTO {schema}.quiz_question_curriculum_outcomes (question_id,outcome_id)
                    VALUES (:question,:outcome) ON CONFLICT DO NOTHING
                """), {"question": question_id, "outcome": outcome_id})
                for extra_outcome in EXTRA_UNIT_OUTCOMES.get(unit.code, ()):
                    conn.execute(sa.text(f"""
                        INSERT INTO {schema}.quiz_question_curriculum_outcomes (question_id,outcome_id)
                        VALUES (:question,:outcome) ON CONFLICT DO NOTHING
                    """), {"question": question_id, "outcome": outcome_ids[extra_outcome]})

    return {"course_id": course_id, "program_id": program_id, "lessons": len(ALL_UNITS),
            "formal_units": len(FORMAL_UNITS), "questions": fixed_question_count()}
