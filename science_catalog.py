"""England-first Primary Science and Chemistry reference courses.

The catalogue is intentionally authored in English and Estonian first.  The
existing localization layer falls back to English for other interface
languages until their reviewed translations are ready.
"""

from __future__ import annotations

import json
from copy import deepcopy

import sqlalchemy as sa


LANGUAGES = ("en", "et")


def _t(en: str, et: str) -> dict[str, str]:
    return {"en": en, "et": et}


def _lesson(en_title: str, et_title: str, en_body: str, et_body: str, *, duration: int = 20, xp: int = 30) -> dict:
    return {
        "title": _t(en_title, et_title), "content_md": _t(en_body, et_body),
        "content_type": "interactive", "duration_min": duration, "xp_reward": xp,
    }


CATALOG = [
    {
        "title": _t("Primary Science", "Loodusõpetus algkoolile"),
        "slug": "primary-science",
        "description": _t(
            "England Years 1–6 science: observe, test, measure and explain the living world, materials, energy and Earth.",
            "Inglismaa 1.–6. klassi loodusõpetus: vaatle, katseta, mõõda ja selgita elusloodust, materjale, energiat ning Maad.",
        ),
        "category": _t("Science", "Loodusõpetus"), "difficulty": "beginner",
        "modules": [
            {"title": _t("Working Scientifically", "Teaduslik uurimine"), "lessons": [
                _lesson("Questions, Tests and Evidence", "Küsimused, katsed ja tõendid",
                    "# Questions, Tests and Evidence\n\nScience begins with a question. Make one change at a time in a fair test, observe carefully, record what happened and use evidence for your conclusion.\n\n## Good investigators\n\n- predict before testing\n- use equipment safely\n- repeat observations when possible\n- say what the evidence does and does not show\n\nA result that surprises you is useful: it gives you a better question to investigate.",
                    "# Küsimused, katsed ja tõendid\n\nTeadus algab küsimusest. Õiglases katses muuda korraga ainult üht asja, vaatle hoolikalt, kirjuta tulemus üles ja põhjenda järeldust tõenditega.\n\n## Hea uurija\n\n- ennustab enne katset\n- kasutab vahendeid ohutult\n- kordab vaatlusi võimalusel\n- ütleb, mida tõendid näitavad ja mida mitte\n\nÜllatav tulemus on kasulik: see annab parema uurimisküsimuse."),
                _lesson("Measuring and Recording", "Mõõtmine ja tulemuste kirjapanek",
                    "# Measuring and Recording\n\nChoose a suitable unit: centimetres for length, grams for mass, seconds for time and degrees Celsius for temperature. Tables and simple graphs help a pattern become visible.\n\nAlways label a measurement and write enough detail for another investigator to understand your work.",
                    "# Mõõtmine ja tulemuste kirjapanek\n\nVali sobiv ühik: pikkuse jaoks sentimeetrid, massi jaoks grammid, aja jaoks sekundid ja temperatuuri jaoks kraadid Celsiuse järgi. Tabelid ja lihtsad graafikud aitavad mustrit märgata.\n\nMärgista mõõtmine alati ning kirjuta piisavalt täpselt, et teine uurija sinu tööst aru saaks.", duration=15),
            ]},
            {"title": _t("Materials and Matter", "Materjalid ja aine"), "lessons": [
                _lesson("Everyday Materials", "Igapäevased materjalid",
                    "# Everyday Materials\n\nObjects are made from materials. Wood, metal, glass, plastic, fabric and rock have properties that make them useful. Compare hardness, flexibility, transparency, absorbency and waterproofing before choosing a material.\n\nA material is not simply “good” or “bad”: it is suitable for a particular job.",
                    "# Igapäevased materjalid\n\nEsemed on tehtud materjalidest. Puidul, metallil, klaasil, plastil, kangal ja kivimil on omadused, mis muudavad need kasulikuks. Võrdle enne materjali valimist kõvadust, painduvust, läbipaistvust, imavust ja veekindlust.\n\nMaterjal ei ole lihtsalt „hea” või „halb”: see sobib kindlaks otstarbeks."),
                _lesson("Particles, States and Changes", "Osakesed, olekud ja muutused",
                    "# Particles, States and Changes\n\nSolids keep their shape because particles are close together. Liquids flow because particles can move past each other. Gases spread to fill a space. Heating gives particles more energy; cooling removes it.\n\nMelting, freezing, evaporation and condensation are changes of state. No new substance is made.",
                    "# Osakesed, olekud ja muutused\n\nTahked ained hoiavad kuju, sest osakesed on lähestikku. Vedelikud voolavad, sest osakesed saavad üksteisest mööduda. Gaasid levivad, et täita ruum. Kuumutamine annab osakestele energiat; jahutamine võtab seda ära.\n\nSulamine, tahkumine, aurumine ja kondenseerumine on olekumuutused. Uut ainet ei teki."),
                _lesson("Mixtures, Solutions and Separation", "Segud, lahused ja eraldamine",
                    "# Mixtures, Solutions and Separation\n\nA mixture contains substances that have not become a new substance. Use a magnet for iron, a sieve for different-sized solids, filtering for an insoluble solid in liquid, and evaporation to recover a dissolved solid.\n\nDissolving is different from melting: salt in water is still salt and water.",
                    "# Segud, lahused ja eraldamine\n\nSegu sisaldab aineid, mis ei ole muutunud uueks aineks. Raua jaoks kasuta magnetit, eri suurusega tahkete ainete jaoks sõela, vees lahustumatu tahke aine jaoks filtreerimist ning lahustunud tahke aine saamiseks aurutamist.\n\nLahustumine erineb sulamisest: sool vees on ikka sool ja vesi."),
            ]},
            {"title": _t("Living World", "Elusloodus"), "lessons": [
                _lesson("Plants, Animals and Habitats", "Taimed, loomad ja elupaigad",
                    "# Plants, Animals and Habitats\n\nLiving things need resources from their habitats. Plants make food using light. Animals depend on plants or other animals. Classify organisms by observable features and explain how a feature helps an organism survive.",
                    "# Taimed, loomad ja elupaigad\n\nElusolendid vajavad oma elupaigast ressursse. Taimed valmistavad valguse abil toitu. Loomad sõltuvad taimedest või teistest loomadest. Rühmita organisme vaadeldavate tunnuste järgi ja selgita, kuidas tunnus aitab ellu jääda."),
                _lesson("Bodies, Growth and Health", "Keha, kasvamine ja tervis",
                    "# Bodies, Growth and Health\n\nHumans and other animals need balanced nutrition, movement and protection from disease. Skeletons support and protect; muscles make movement possible. Living things grow, reproduce and change over time.",
                    "# Keha, kasvamine ja tervis\n\nInimesed ja teised loomad vajavad tasakaalustatud toitu, liikumist ning kaitset haiguste eest. Luustik toetab ja kaitseb; lihased võimaldavad liikumist. Elusolendid kasvavad, paljunevad ja muutuvad aja jooksul."),
            ]},
            {"title": _t("Energy, Earth and Space", "Energia, Maa ja kosmos"), "lessons": [
                _lesson("Light, Sound and Electricity", "Valgus, heli ja elekter",
                    "# Light, Sound and Electricity\n\nLight travels from sources and reflects from surfaces. Sound is made by vibrations. A complete electrical circuit lets current flow; switches open or close the circuit. Use measurements to compare brightness, volume or distance.",
                    "# Valgus, heli ja elekter\n\nValgus levib allikatest ja peegeldub pindadelt. Heli tekib võnkumisest. Terviklik elektriahel laseb voolul liikuda; lüliti avab või sulgeb ahela. Kasuta mõõtmisi heleduse, valjuse või kauguse võrdlemiseks."),
                _lesson("Earth, Space and Forces", "Maa, kosmos ja jõud",
                    "# Earth, Space and Forces\n\nThe Earth orbits the Sun and rotates once each day. Gravity pulls objects towards Earth. Pushes and pulls can change an object’s motion or shape. Rocks and soils tell stories about processes that change Earth over long periods.",
                    "# Maa, kosmos ja jõud\n\nMaa tiirleb ümber Päikese ning pöörleb kord ööpäevas. Raskusjõud tõmbab objekte Maa poole. Tõuked ja tõmbed võivad muuta objekti liikumist või kuju. Kivimid ja mullad jutustavad protsessidest, mis muudavad Maad pikkade ajavahemike jooksul."),
            ]},
        ],
    },
    {
        "title": _t("Chemistry Fundamentals", "Keemia alused"), "slug": "chemistry-fundamentals",
        "description": _t("England KS3–GCSE chemistry: particles, atoms, bonding, reactions, quantitative chemistry and Earth resources.", "Inglismaa KS3–GCSE keemia: osakesed, aatomid, sidemed, reaktsioonid, arvutuskeemia ja Maa ressursid."),
        "category": _t("Chemistry", "Keemia"), "difficulty": "intermediate",
        "modules": [
            {"title": _t("Particles, Atoms and the Periodic Table", "Osakesed, aatomid ja perioodilisustabel"), "lessons": [
                _lesson("Particle Model and Changes of State", "Osakeste mudel ja olekumuutused", "# Particle Model and Changes of State\n\nUse particle motion and energy transfers to explain density, gas pressure, diffusion and changes of state. A chemical reaction rearranges atoms; a physical change does not create a new substance.", "# Osakeste mudel ja olekumuutused\n\nKasuta osakeste liikumist ja energiaülekandeid tiheduse, gaasirõhu, difusiooni ning olekumuutuste selgitamiseks. Keemiline reaktsioon korraldab aatomeid ümber; füüsikaline muutus uut ainet ei tekita."),
                _lesson("Atoms, Ions and Isotopes", "Aatomid, ioonid ja isotoobid", "# Atoms, Ions and Isotopes\n\nAtomic number is the number of protons. Mass number counts protons and neutrons. Atoms form ions by gaining or losing electrons. Isotopes are atoms of one element with different numbers of neutrons.", "# Aatomid, ioonid ja isotoobid\n\nAatomnumber on prootonite arv. Massiarv loeb prootoneid ja neutroneid. Aatomid moodustavad ioone elektrone loovutades või vastu võttes. Isotoobid on sama elemendi aatomid erineva neutronite arvuga."),
                _lesson("Periodic Table and Reactivity", "Perioodilisustabel ja reaktsioonivõime", "# Periodic Table and Reactivity\n\nElements are arranged by atomic number. Groups have related outer-electron patterns; periods show occupied shells. Use position to predict simple ion charge and trends in reactivity.", "# Perioodilisustabel ja reaktsioonivõime\n\nElemendid on paigutatud aatomnumbri järgi. Rühmadel on sarnased väliselektronide mustrid; perioodid näitavad hõivatud elektronkihte. Kasuta asukohta lihtsa ioonlaengu ja reaktsioonivõime suundumuste ennustamiseks."),
            ]},
            {"title": _t("Bonding and Properties", "Sidemed ja omadused"), "lessons": [
                _lesson("Ionic, Covalent and Metallic Bonding", "Ioon-, kovalentne ja metalliline side", "# Ionic, Covalent and Metallic Bonding\n\nIonic bonds are attractions between oppositely charged ions. Covalent bonds share electrons. Metallic bonding involves positive ions and delocalised electrons. Structure explains melting point, conductivity and solubility.", "# Ioon-, kovalentne ja metalliline side\n\nIoonside on vastasmärgiliste ioonide vaheline tõmme. Kovalentne side jagab elektrone. Metallilises sidemes on positiivsed ioonid ja delokaliseeritud elektronid. Struktuur selgitab sulamispunkti, juhtivust ja lahustuvust."),
                _lesson("Giant Structures and Materials", "Hiigelstruktuurid ja materjalid", "# Giant Structures and Materials\n\nDiamond, graphite, graphene, metals and ionic lattices have different particle arrangements. Relate each arrangement to strength, hardness, conductivity and uses.", "# Hiigelstruktuurid ja materjalid\n\nTeemandil, grafiidil, grafeenil, metallidel ja ioonvõredel on erinev osakeste paigutus. Seo iga paigutus tugevuse, kõvaduse, juhtivuse ja kasutusaladega."),
            ]},
            {"title": _t("Reactions and Quantitative Chemistry", "Reaktsioonid ja arvutuskeemia"), "lessons": [
                _lesson("Equations and Conservation", "Võrrandid ja jäävusseadus", "# Equations and Conservation\n\nBalanced symbol equations conserve atoms. Coefficients change amounts, never the chemical formula. Include state symbols when useful and identify reactants and products.", "# Võrrandid ja jäävusseadus\n\nTasakaalustatud sümbolvõrrandid säilitavad aatomite arvu. Kordajad muudavad koguseid, mitte kunagi keemilist valemit. Vajadusel lisa olekusümbolid ning erista lähteained ja saadused."),
                _lesson("Moles, Masses and Concentration", "Moolid, massid ja kontsentratsioon", "# Moles, Masses and Concentration\n\nThe mole links mass, particle number and formula mass. Use a balanced equation as a ratio to calculate reacting masses, gas volumes, concentration and yield. Show units at every step.", "# Moolid, massid ja kontsentratsioon\n\nMool seob massi, osakeste arvu ja valemmassi. Kasuta tasakaalustatud võrrandit suhtena reageerivate masside, gaasimahtude, kontsentratsiooni ja saagise arvutamiseks. Näita ühikuid igal sammul."),
                _lesson("Acids, Bases, Redox and Electrolysis", "Happed, alused, redoks ja elektrolüüs", "# Acids, Bases, Redox and Electrolysis\n\nAcids react with metals, bases and carbonates. Neutralisation makes salt and water. Redox transfers electrons. Electrolysis uses electrical energy to decompose ionic compounds.", "# Happed, alused, redoks ja elektrolüüs\n\nHapped reageerivad metallide, aluste ja karbonaatidega. Neutraliseerimine annab soola ja vee. Redoksreaktsioonis kanduvad elektronid üle. Elektrolüüs kasutab elektrienergiat ioonsete ühendite lagundamiseks."),
            ]},
            {"title": _t("Energy, Rates and Resources", "Energia, kiirused ja ressursid"), "lessons": [
                _lesson("Energy Changes and Reaction Rates", "Energiimuutused ja reaktsioonikiirused", "# Energy Changes and Reaction Rates\n\nExothermic reactions transfer energy to surroundings; endothermic reactions take it in. Collision theory explains why temperature, concentration, surface area and catalysts change rate.", "# Energiimuutused ja reaktsioonikiirused\n\nEksotermilised reaktsioonid annavad energiat ümbritsevale; endotermilised võtavad seda sisse. Põrgeteooria selgitab, miks temperatuur, kontsentratsioon, pindala ja katalüsaatorid muudavad kiirust."),
                _lesson("Earth Chemistry, Organic Chemistry and Analysis", "Maa keemia, orgaaniline keemia ja analüüs", "# Earth Chemistry, Organic Chemistry and Analysis\n\nChemistry helps use finite resources responsibly. Carbon compounds form families with related reactions. Learn basic tests for gases and ions, chromatography and the difference between pure substances and mixtures.", "# Maa keemia, orgaaniline keemia ja analüüs\n\nKeemia aitab kasutada piiratud ressursse vastutustundlikult. Süsinikuühendid moodustavad sarnaste reaktsioonidega perekondi. Õpi gaaside ja ioonide põhiteste, kromatograafiat ning puhaste ainete ja segude erinevust."),
            ]},
        ],
    },
    {
        "title": _t("Advanced Chemistry", "Edasijõudnute keemia"), "slug": "advanced-chemistry",
        "description": _t("A-level to first-year university bridge in physical, organic and inorganic chemistry with practical data skills.", "Sild A-taseme ja ülikooli esimese aasta vahel füüsikalises, orgaanilises ja anorgaanilises keemias ning praktilistes andmeoskustes."),
        "category": _t("Chemistry", "Keemia"), "difficulty": "advanced",
        "modules": [
            {"title": _t("Physical Chemistry", "Füüsikaline keemia"), "lessons": [
                _lesson("Orbitals, Spectra and Structure", "Orbitaalid, spektrid ja struktuur", "# Orbitals, Spectra and Structure\n\nUse sub-shells, orbitals and electron configuration to explain periodicity. Interpret simple mass spectra and link molecular shape to electron-pair repulsion.", "# Orbitaalid, spektrid ja struktuur\n\nKasuta alamkihte, orbitaale ja elektronkonfiguratsiooni perioodilisuse selgitamiseks. Tõlgenda lihtsaid massispektreid ning seo molekuli kuju elektronpaaride tõukumisega."),
                _lesson("Thermodynamics, Kinetics and Equilibrium", "Termodünaamika, kineetika ja tasakaal", "# Thermodynamics, Kinetics and Equilibrium\n\nUse enthalpy, entropy and free-energy ideas to reason about feasibility. Model rates with rate equations and activation energy. At equilibrium, forward and reverse rates are equal; use Kc and Le Chatelier’s principle carefully.", "# Termodünaamika, kineetika ja tasakaal\n\nKasuta entalpia, entroopia ja vabaenergia ideid reaktsioonide võimalikkuse põhjendamiseks. Modelleeri kiirusi kiirusvõrrandite ja aktiveerimisenergiaga. Tasakaalus on edasi- ja tagasireaktsiooni kiirused võrdsed; kasuta Kc-d ja Le Chatelier’ printsiipi hoolikalt."),
                _lesson("Acids, Electrochemistry and Measurement", "Happed, elektrokeemia ja mõõtmine", "# Acids, Electrochemistry and Measurement\n\nCalculate pH, Ka and buffer behaviour with assumptions stated. Build cell diagrams, compare electrode potentials and report uncertainty, significant figures and anomalous data honestly.", "# Happed, elektrokeemia ja mõõtmine\n\nArvuta pH, Ka ja puhverlahuste käitumine koos eeldustega. Koosta elemendiskeeme, võrdle elektroodipotentsiaale ning esita määramatus, tüvenumbrid ja hälbivad andmed ausalt."),
            ]},
            {"title": _t("Organic Chemistry I", "Orgaaniline keemia I"), "lessons": [
                _lesson("Structure, Stereochemistry and Naming", "Struktuur, stereokeemia ja nimetamine", "# Structure, Stereochemistry and Naming\n\nRepresent organic compounds with displayed, structural and skeletal formulas. Identify functional groups, homologous series, stereocentres and E/Z or cis/trans isomerism where appropriate.", "# Struktuur, stereokeemia ja nimetamine\n\nEsita orgaanilisi ühendeid välja kirjutatud, struktuuri- ja skeletivalemiga. Tuvasta funktsionaalrühmad, homoloogilised read, stereokeskmed ning vajadusel E/Z või cis/trans isomeeria."),
                _lesson("Mechanisms and Synthesis", "Mehhanismid ja süntees", "# Mechanisms and Synthesis\n\nUse curly arrows to account for electron pairs in substitution, elimination, addition and carbonyl reactions. Plan short syntheses by tracking functional-group changes, selectivity, yield and purification.", "# Mehhanismid ja süntees\n\nKasuta kaarnoolekesi elektronpaaride liikumise kirjeldamiseks asendus-, eliminatsiooni-, liitumis- ja karbonüülreaktsioonides. Plaani lühisünteese, jälgides funktsionaalrühmade muutusi, selektiivsust, saagist ja puhastamist."),
                _lesson("Spectroscopy and Structure Elucidation", "Spektroskoopia ja struktuuri määramine", "# Spectroscopy and Structure Elucidation\n\nCombine accurate mass, fragmentation, infrared absorption and 1H/13C NMR evidence. A proposed structure is credible only when every major datum is explained.", "# Spektroskoopia ja struktuuri määramine\n\nÜhenda täpne mass, fragmenteerumine, infrapunaneeldumine ning 1H/13C NMR-i tõendid. Pakutud struktuur on usutav vaid siis, kui iga oluline andmepunkt on selgitatud."),
            ]},
            {"title": _t("Inorganic Chemistry I", "Anorgaaniline keemia I"), "lessons": [
                _lesson("Periodicity and Redox", "Perioodilisus ja redoks", "# Periodicity and Redox\n\nExplain trends using nuclear charge, shielding and structure. Balance redox equations with oxidation states and consider why chemical choices have environmental and industrial consequences.", "# Perioodilisus ja redoks\n\nSelgita suundumusi tuumalaengu, varjestuse ja struktuuriga. Tasakaalusta redoksvõrrandeid oksüdatsiooniastmete abil ning mõtle, miks keemilistel valikutel on keskkonna- ja tööstuslikud tagajärjed."),
                _lesson("Coordination Chemistry and Materials", "Koordinatsioonikeemia ja materjalid", "# Coordination Chemistry and Materials\n\nDescribe ligands, coordination number, geometry, isomerism and colour in transition-metal complexes. Relate crystal and solid-state structure to magnetic, optical and conductive properties.", "# Koordinatsioonikeemia ja materjalid\n\nKirjelda ligande, koordinatsiooniarvu, geomeetriat, isomeeriat ja värvust siirdemetallikompleksides. Seo kristall- ja tahkisstruktuur magnetiliste, optiliste ning juhtivusomadustega."),
            ]},
            {"title": _t("Practical Chemistry and Data", "Praktiline keemia ja andmed"), "lessons": [
                _lesson("Designing Reliable Investigations", "Usaldusväärsete uurimuste kavandamine", "# Designing Reliable Investigations\n\nChoose controls, measurements and a safe method that answer a focused question. Distinguish accuracy, precision, repeatability and reproducibility. Use uncertainty to judge a claim rather than hiding imperfect data.", "# Usaldusväärsete uurimuste kavandamine\n\nVali kontrollid, mõõtmised ja ohutu meetod, mis vastavad täpsele küsimusele. Erista täpsust, kordustäpsust ja reprodutseeritavust. Kasuta määramatust väite hindamiseks, mitte ebatäiuslike andmete peitmiseks."),
            ]},
        ],
    },
]


def _review(
    key: str,
    course_slug: str,
    lesson: str,
    difficulty_band: int,
    concept: str,
    question_en: str,
    question_et: str,
    options_en: list[str],
    options_et: list[str],
    correct_index: int,
    explanation_en: str,
    explanation_et: str,
) -> dict:
    return {
        "source_key": f"fl-review-{key}",
        "course_slug": course_slug,
        "lesson": lesson,
        "difficulty_band": difficulty_band,
        "concepts": [concept],
        "question": _t(question_en, question_et),
        "options": _t(options_en, options_et),
        "correct_index": correct_index,
        "explanation": _t(explanation_en, explanation_et),
    }


# Every science lesson gets an original, answer-safe multiple-choice review.
# The same authored record powers Classic quizzes and a structured Chat activity,
# keeping both modes aligned in English and Estonian.
REVIEW_QUESTIONS = [
    _review(
        "primary-fair-test", "primary-science", "Questions, Tests and Evidence", 1, "fair-tests",
        "What should you change in a fair test?", "Mida tuleks õiglases katses muuta?",
        ["One variable at a time", "Everything at once", "The result after testing"],
        ["Üht muutujat korraga", "Kõike korraga", "Tulemust pärast katset"], 0,
        "Changing one variable makes the evidence easier to interpret.",
        "Ühe muutuja muutmine muudab tõendite tõlgendamise lihtsamaks.",
    ),
    _review(
        "primary-measurement-unit", "primary-science", "Measuring and Recording", 1, "measurement",
        "Which unit is suitable for recording temperature?", "Milline ühik sobib temperatuuri märkimiseks?",
        ["Degrees Celsius", "Grams", "Seconds"], ["Celsiuse kraadid", "Grammid", "Sekundid"], 0,
        "Temperature is commonly recorded in degrees Celsius.", "Temperatuuri märgitakse tavaliselt Celsiuse kraadides.",
    ),
    _review(
        "primary-materials", "primary-science", "Everyday Materials", 1, "materials",
        "Which material property matters most for a raincoat?", "Milline materjali omadus on vihmamantli puhul kõige tähtsam?",
        ["Waterproof", "Absorbent", "Brittle"], ["Veekindel", "Imav", "Habras"], 0,
        "A raincoat should resist water rather than absorb it.", "Vihmamantel peaks vett tõrjuma, mitte seda imama.",
    ),
    _review(
        "primary-particles", "primary-science", "Particles, States and Changes", 1, "states-of-matter",
        "What happens to the substance when ice melts?", "Mis juhtub ainega jää sulamisel?",
        ["It changes state", "A new substance forms", "Its particles disappear"],
        ["See muudab olekut", "Tekib uus aine", "Selle osakesed kaovad"], 0,
        "Melting is a physical change of state; no new substance forms.",
        "Sulamine on füüsikaline olekumuutus; uut ainet ei teki.",
    ),
    _review(
        "primary-separation", "primary-science", "Mixtures, Solutions and Separation", 1, "separation",
        "Which method separates insoluble sand from water?", "Milline meetod eraldab vees lahustumatu liiva?",
        ["Filtering", "Melting", "Using a magnet"], ["Filtreerimine", "Sulatamine", "Magneti kasutamine"], 0,
        "A filter traps the insoluble solid while the water passes through.",
        "Filter püüab lahustumatu tahke aine kinni, samal ajal kui vesi läbib filtri.",
    ),
    _review(
        "primary-habitats", "primary-science", "Plants, Animals and Habitats", 1, "habitats",
        "What do green plants use to make food?", "Mida kasutavad rohelised taimed toidu valmistamiseks?",
        ["Light", "Sound", "Moonlight only"], ["Valgust", "Heli", "Ainult kuuvalgust"], 0,
        "Plants use light energy to make food by photosynthesis.", "Taimed kasutavad fotosünteesis toidu valmistamiseks valgusenergiat.",
    ),
    _review(
        "primary-bodies", "primary-science", "Bodies, Growth and Health", 1, "skeletons",
        "What is one function of the skeleton?", "Mis on luustiku üks ülesanne?",
        ["Support and protect the body", "Make all food", "Pump blood"],
        ["Keha toetamine ja kaitsmine", "Kogu toidu valmistamine", "Vere pumpamine"], 0,
        "The skeleton supports the body and protects organs.", "Luustik toetab keha ja kaitseb elundeid.",
    ),
    _review(
        "primary-energy", "primary-science", "Light, Sound and Electricity", 1, "sound",
        "What produces sound?", "Mis tekitab heli?",
        ["Vibrations", "Stillness", "A broken circuit"], ["Võnkumine", "Paigalseis", "Katkine vooluring"], 0,
        "Sound begins when something vibrates.", "Heli tekib siis, kui miski võngub.",
    ),
    _review(
        "primary-earth", "primary-science", "Earth, Space and Forces", 1, "earth-rotation",
        "Which movement of Earth gives us day and night?", "Milline Maa liikumine põhjustab päeva ja öö vaheldumise?",
        ["Rotation on its axis", "Its orbit around the Sun", "The Moon's orbit"],
        ["Pöörlemine ümber telje", "Tiirlemine ümber Päikese", "Kuu tiirlemine"], 0,
        "Earth rotates once in about 24 hours, producing day and night.",
        "Maa pöörleb umbes 24 tunniga ühe korra, põhjustades päeva ja öö vaheldumise.",
    ),
    _review(
        "chem-particle-model", "chemistry-fundamentals", "Particle Model and Changes of State", 2, "particle-model",
        "What distinguishes a chemical reaction from a change of state?", "Mis eristab keemilist reaktsiooni olekumuutusest?",
        ["Atoms are rearranged into new substances", "Particles stop moving", "Mass always disappears"],
        ["Aatomid paigutuvad ümber uuteks aineteks", "Osakesed lakkavad liikumast", "Mass kaob alati"], 0,
        "Chemical reactions rearrange atoms; changes of state do not make a new substance.",
        "Keemilised reaktsioonid paigutavad aatomeid ümber; olekumuutus uut ainet ei tekita.",
    ),
    _review(
        "chem-atoms", "chemistry-fundamentals", "Atoms, Ions and Isotopes", 2, "atomic-structure",
        "What does an element's atomic number equal?", "Millega võrdub elemendi aatomnumber?",
        ["Number of protons", "Number of neutrons", "Protons plus neutrons"],
        ["Prootonite arv", "Neutronite arv", "Prootonite ja neutronite summa"], 0,
        "Atomic number is defined by the number of protons in the nucleus.",
        "Aatomnumbri määrab prootonite arv tuumas.",
    ),
    _review(
        "chem-periodic", "chemistry-fundamentals", "Periodic Table and Reactivity", 2, "periodicity",
        "Why do elements in the same group often react similarly?", "Miks reageerivad sama rühma elemendid sageli sarnaselt?",
        ["They have related outer-electron patterns", "They have identical masses", "They are all gases"],
        ["Neil on sarnane väliselektronide paigutus", "Neil on ühesugune mass", "Nad on kõik gaasid"], 0,
        "Outer electrons strongly influence bonding and reactivity.", "Väliselektronid mõjutavad tugevalt sidemeid ja reaktsioonivõimet.",
    ),
    _review(
        "chem-bonding", "chemistry-fundamentals", "Ionic, Covalent and Metallic Bonding", 2, "bonding",
        "What happens in a covalent bond?", "Mis toimub kovalentses sidemes?",
        ["Electrons are shared", "Neutrons are transferred", "Atoms lose all particles"],
        ["Elektrone jagatakse", "Neutroneid antakse üle", "Aatomid kaotavad kõik osakesed"], 0,
        "A covalent bond is a shared pair of electrons.", "Kovalentne side on jagatud elektronpaar.",
    ),
    _review(
        "chem-giant", "chemistry-fundamentals", "Giant Structures and Materials", 2, "giant-structures",
        "Why can graphite conduct electricity?", "Miks juhib grafiit elektrit?",
        ["It has delocalised electrons", "It contains liquid metal", "Its atoms are ionic"],
        ["Selles on delokaliseeritud elektronid", "See sisaldab vedelat metalli", "Selle aatomid on ioonsed"], 0,
        "Delocalised electrons can move through graphite's layered structure.",
        "Delokaliseeritud elektronid saavad liikuda läbi grafiidi kihilise struktuuri.",
    ),
    _review(
        "chem-equations", "chemistry-fundamentals", "Equations and Conservation", 2, "balanced-equations",
        "What may be changed when balancing a symbol equation?", "Mida võib sümbolvõrrandi tasakaalustamisel muuta?",
        ["Coefficients", "Chemical formula subscripts", "Element symbols"],
        ["Kordajaid", "Keemilise valemi alaindekseid", "Elementide sümboleid"], 0,
        "Coefficients change amounts while chemical formulas remain fixed.",
        "Kordajad muudavad koguseid, kuid keemilised valemid jäävad samaks.",
    ),
    _review(
        "chem-moles", "chemistry-fundamentals", "Moles, Masses and Concentration", 3, "moles",
        "How many moles are in 36.0 g of water when Mr = 18.0?", "Mitu mooli on 36,0 g vees, kui Mr = 18,0?",
        ["2.0 mol", "0.5 mol", "18 mol"], ["2,0 mol", "0,5 mol", "18 mol"], 0,
        "Amount = mass / Mr = 36.0 / 18.0 = 2.0 mol.", "Ainehulk = mass / Mr = 36,0 / 18,0 = 2,0 mol.",
    ),
    _review(
        "chem-acids", "chemistry-fundamentals", "Acids, Bases, Redox and Electrolysis", 3, "acids",
        "Which ion is associated with acidity in aqueous solution?", "Milline ioon on vesilahuse happelisusega seotud?",
        ["H+", "Na+", "Cl−"], ["H+", "Na+", "Cl−"], 0,
        "Acids produce hydrogen ions, H+, in aqueous solution.", "Happed annavad vesilahuses vesinikioone H+.",
    ),
    _review(
        "chem-rates", "chemistry-fundamentals", "Energy Changes and Reaction Rates", 3, "reaction-rates",
        "How does a catalyst increase reaction rate?", "Kuidas suurendab katalüsaator reaktsioonikiirust?",
        ["It lowers activation energy", "It raises product mass", "It changes the final equilibrium yield"],
        ["See vähendab aktivatsioonienergiat", "See suurendab saaduse massi", "See muudab tasakaalulist lõppsaagist"], 0,
        "A catalyst provides an alternative pathway with lower activation energy.",
        "Katalüsaator pakub väiksema aktivatsioonienergiaga alternatiivset reaktsiooniteed.",
    ),
    _review(
        "chem-analysis", "chemistry-fundamentals", "Earth Chemistry, Organic Chemistry and Analysis", 3, "analysis",
        "What can chromatography help separate?", "Mida aitab kromatograafia eraldada?",
        ["Components of a mixture", "Protons from a nucleus", "Energy from mass"],
        ["Segu koostisosi", "Prootoneid tuumast", "Energiat massist"], 0,
        "Chromatography separates mixture components by their different movement between phases.",
        "Kromatograafia eraldab segu koostisosi nende erineva liikumise järgi faaside vahel.",
    ),
    _review(
        "legacy-atoms", "chemistry-fundamentals", "Atoms and the Periodic Table", 2, "atomic-structure",
        "Which particle determines an element's identity?", "Milline osake määrab elemendi?",
        ["Proton", "Neutron", "Electron shell"], ["Prooton", "Neutron", "Elektronkiht"], 0,
        "The proton count is the atomic number and identifies the element.", "Prootonite arv on aatomnumber ja määrab elemendi.",
    ),
    _review(
        "legacy-reactions", "chemistry-fundamentals", "Types of Reactions and Balancing Equations", 2, "balanced-equations",
        "Why must a chemical equation be balanced?", "Miks peab keemiline võrrand olema tasakaalus?",
        ["Atoms are conserved", "Every coefficient must be one", "Products must weigh nothing"],
        ["Aatomite arv säilib", "Iga kordaja peab olema üks", "Saadused ei tohi midagi kaaluda"], 0,
        "Balancing shows that each type of atom is conserved.", "Tasakaalustamine näitab, et iga liiki aatomite arv säilib.",
    ),
    _review(
        "advanced-orbitals", "advanced-chemistry", "Orbitals, Spectra and Structure", 4, "spectra",
        "What produces an atomic emission line?", "Mis tekitab aatomi emissioonijoone?",
        ["An electron drops between energy levels", "A neutron leaves the nucleus", "An orbital gains mass"],
        ["Elektron langeb energiatasemete vahel", "Neutron lahkub tuumast", "Orbitaal omandab massi"], 0,
        "A photon is emitted when an electron falls to a lower energy level.",
        "Footon kiirgub, kui elektron langeb madalamale energiatasemele.",
    ),
    _review(
        "advanced-equilibrium", "advanced-chemistry", "Thermodynamics, Kinetics and Equilibrium", 4, "equilibrium",
        "What does a catalyst do to an equilibrium position?", "Mida teeb katalüsaator tasakaaluasendiga?",
        ["It does not change it", "It shifts it fully to products", "It stops the reverse reaction"],
        ["See ei muuda seda", "See nihutab selle täielikult saaduste poole", "See peatab pöördreaktsiooni"], 0,
        "A catalyst speeds forward and reverse reactions equally, so the equilibrium position is unchanged.",
        "Katalüsaator kiirendab edasi- ja pöördreaktsiooni võrdselt, seega tasakaaluasend ei muutu.",
    ),
    _review(
        "advanced-electrochem", "advanced-chemistry", "Acids, Electrochemistry and Measurement", 4, "electrochemistry",
        "How is a standard cell potential calculated from reduction potentials?", "Kuidas arvutatakse standardpotentsiaal redutseerumispotentsiaalidest?",
        ["Cathode minus anode", "Anode minus cathode", "Cathode plus anode in every case"],
        ["Katood miinus anood", "Anood miinus katood", "Alati katood pluss anood"], 0,
        "Using reduction potentials, E°cell = E°cathode − E°anode.", "Redutseerumispotentsiaalide korral E°element = E°katood − E°anood.",
    ),
    _review(
        "advanced-stereochemistry", "advanced-chemistry", "Structure, Stereochemistry and Naming", 4, "isomerism",
        "What do structural isomers share?", "Mis on struktuuriisomeeridel ühine?",
        ["Molecular formula", "Atom connectivity", "Every physical property"],
        ["Molekulivalem", "Aatomite ühendusviis", "Kõik füüsikalised omadused"], 0,
        "Structural isomers have the same molecular formula but different connectivity.",
        "Struktuuriisomeeridel on sama molekulivalem, kuid erinev aatomite ühendusviis.",
    ),
    _review(
        "advanced-mechanisms", "advanced-chemistry", "Mechanisms and Synthesis", 4, "mechanisms",
        "What does a curly arrow represent in an organic mechanism?", "Mida näitab kaarnool orgaanilises mehhanismis?",
        ["Movement of an electron pair", "Movement of an atom's mass", "Heat leaving the flask"],
        ["Elektronpaari liikumist", "Aatomi massi liikumist", "Soojuse lahkumist kolvist"], 0,
        "A full curly arrow tracks the movement of an electron pair.", "Täielik kaarnool jälgib elektronpaari liikumist.",
    ),
    _review(
        "advanced-spectroscopy", "advanced-chemistry", "Spectroscopy and Structure Elucidation", 4, "infrared",
        "A broad infrared O–H absorption most strongly suggests which group?", "Millisele rühmale viitab kõige tugevamalt lai O–H neeldumisriba infrapunaspektris?",
        ["Alcohol", "Alkene", "Halogenoalkane"], ["Alkohol", "Alkeen", "Halogenoalkaan"], 0,
        "Alcohol O–H bonds commonly give a broad infrared absorption.", "Alkoholi O–H side annab tavaliselt laia infrapunase neeldumisriba.",
    ),
    _review(
        "advanced-redox", "advanced-chemistry", "Periodicity and Redox", 4, "redox",
        "What is oxidation in electron-transfer terms?", "Mis on oksüdatsioon elektronide ülekande mõttes?",
        ["Loss of electrons", "Gain of electrons", "No change in oxidation state"],
        ["Elektronide loovutamine", "Elektronide liitmine", "Oksüdatsiooniastme muutumatus"], 0,
        "Oxidation is loss of electrons; reduction is gain.", "Oksüdatsioon on elektronide loovutamine; redutseerumine on nende liitmine.",
    ),
    _review(
        "advanced-coordination", "advanced-chemistry", "Coordination Chemistry and Materials", 4, "coordination",
        "What does a ligand donate to a metal centre?", "Mida loovutab ligand metallitsentrile?",
        ["A lone pair of electrons", "A neutron pair", "Its entire nucleus"],
        ["Üksiku elektronpaari", "Neutronpaari", "Kogu oma tuuma"], 0,
        "A ligand forms a coordinate bond by donating a lone pair.", "Ligand moodustab koordinatsioonisideme üksiku elektronpaari loovutamisega.",
    ),
    _review(
        "advanced-investigations", "advanced-chemistry", "Designing Reliable Investigations", 4, "reliability",
        "What does repeatability mean?", "Mida tähendab korratavus?",
        ["The same person gets similar results using the same method and equipment", "Any result matches a prediction", "A different method gives a larger value"],
        ["Sama inimene saab sama meetodi ja varustusega sarnaseid tulemusi", "Iga tulemus vastab ennustusele", "Erinev meetod annab suurema väärtuse"], 0,
        "Repeatability concerns repeated measurements under the same conditions.",
        "Korratavus tähendab mõõtmiste kordamist samades tingimustes.",
    ),
]


EXERCISES = [
    {
        "source_key": "fl-primary-particle-state", "course_slug": "primary-science", "lesson": "Particles, States and Changes",
        "exercise_type": "molecule_geometry", "concepts": ["states-of-matter", "particle-model"], "difficulty_band": 1,
        "prompt": _t("Warm the model, then choose the state where particles are closest together.", "Soojenda mudelit, seejärel vali olek, kus osakesed on kõige lähestikku."),
        "public": {"choices": _t(["Solid", "Liquid", "Gas"], ["Tahke", "Vedelik", "Gaas"]), "choice_labels": _t(["Solid", "Liquid", "Gas"], ["Tahke", "Vedelik", "Gaas"]), "molecule": "water", "scene": "particle-state", "ui": _t({"check": "Check answer", "reset": "Reset view", "heat": "Heat", "cool": "Cool", "level": "Guided science"}, {"check": "Kontrolli vastust", "reset": "Lähtesta vaade", "heat": "Soojenda", "cool": "Jahuta", "level": "Juhendatud loodusõpetus"})},
        "answer": {"choice": 0, "feedback": _t(
            {"correct_answer": "Solid", "explanation": "Particles in a solid are packed most closely and vibrate about fixed positions."},
            {"correct_answer": "Tahke", "explanation": "Tahkes aines paiknevad osakesed kõige tihedamalt ja võnguvad kindlate asendite ümber."},
        )},
    },
    {
        "source_key": "fl-primary-material-choice", "course_slug": "primary-science", "lesson": "Everyday Materials",
        "exercise_type": "material_sort", "concepts": ["materials", "properties"], "difficulty_band": 1,
        "prompt": _t("Choose the best material for a waterproof raincoat.", "Vali veekindla vihmamantli jaoks parim materjal."),
        "public": {"choices": _t(["Absorbent paper", "Waterproof fabric", "Glass"], ["Imav paber", "Veekindel kangas", "Klaas"]), "ui": _t({"check": "Check answer", "level": "Guided science"}, {"check": "Kontrolli vastust", "level": "Juhendatud loodusõpetus"})},
        "answer": {"choice": 1, "feedback": _t(
            {"correct_answer": "Waterproof fabric", "explanation": "A raincoat must resist water while remaining flexible enough to wear."},
            {"correct_answer": "Veekindel kangas", "explanation": "Vihmamantel peab vett tõrjuma ja olema kandmiseks piisavalt painduv."},
        )},
    },
    {
        "source_key": "fl-chem-atom-sodium", "course_slug": "chemistry-fundamentals", "lesson": "Atoms, Ions and Isotopes",
        "exercise_type": "atom_builder", "concepts": ["atomic-structure", "ions"], "difficulty_band": 2,
        "prompt": _t("Build a neutral sodium-23 atom: choose its protons, neutrons and electrons.", "Koosta neutraalne naatrium-23 aatom: vali prootonite, neutronite ja elektronide arv."),
        "public": {"atom": "Na", "mass_number": 23, "atomic_number": 11, "ui": _t({"check": "Check atom", "level": "Guided chemistry", "protons": "Protons", "neutrons": "Neutrons", "electrons": "Electrons"}, {"check": "Kontrolli aatomit", "level": "Juhendatud keemia", "protons": "Prootonid", "neutrons": "Neutronid", "electrons": "Elektronid"})},
        "answer": {"protons": 11, "neutrons": 12, "electrons": 11, "feedback": _t(
            {"correct_answer": "11 protons, 12 neutrons and 11 electrons", "explanation": "Sodium has atomic number 11; a neutral atom has 11 electrons, and sodium-23 has 23 − 11 = 12 neutrons."},
            {"correct_answer": "11 prootonit, 12 neutronit ja 11 elektroni", "explanation": "Naatriumi aatomnumber on 11; neutraalsel aatomil on 11 elektroni ning naatrium-23-l on 23 − 11 = 12 neutronit."},
        )},
    },
    {
        "source_key": "fl-chem-balance-water", "course_slug": "chemistry-fundamentals", "lesson": "Equations and Conservation",
        "exercise_type": "equation_balance", "concepts": ["balanced-equations", "conservation"], "difficulty_band": 2,
        "prompt": _t("Balance the equation H₂ + O₂ → H₂O. Enter coefficients from left to right.", "Tasakaalusta võrrand H₂ + O₂ → H₂O. Sisesta kordajad vasakult paremale."),
        "public": {"equation": ["H₂", "O₂", "H₂O"], "ui": _t({"check": "Check equation", "level": "Guided chemistry", "coefficient": "Coefficient"}, {"check": "Kontrolli võrrandit", "level": "Juhendatud keemia", "coefficient": "Kordaja"})},
        "answer": {"coefficients": [2, 1, 2], "feedback": _t(
            {"correct_answer": "2H₂ + O₂ → 2H₂O", "explanation": "These coefficients give four hydrogen atoms and two oxygen atoms on both sides, conserving each element."},
            {"correct_answer": "2H₂ + O₂ → 2H₂O", "explanation": "Nende kordajatega on mõlemal pool neli vesiniku- ja kaks hapnikuaatomit, seega säilib iga element."},
        )},
    },
    {
        "source_key": "fl-chem-water-geometry", "course_slug": "chemistry-fundamentals", "lesson": "Ionic, Covalent and Metallic Bonding",
        "exercise_type": "molecule_geometry", "concepts": ["covalent-bonding", "molecular-shape"], "difficulty_band": 2,
        "prompt": _t("Inspect water in 3D. Which description fits its bonding?", "Uuri vett 3D-s. Milline kirjeldus sobib selle sidemega?"),
        "public": {"choices": _t(["Covalent bonds share electrons", "Ionic bonds transfer all atoms", "Metallic bonds form molecules"], ["Kovalentne side jagab elektrone", "Ioonside kannab üle kõik aatomid", "Metalliline side moodustab molekule"]), "molecule": "water", "scene": "molecule", "ui": _t({"check": "Check answer", "reset": "Reset view", "level": "Guided chemistry"}, {"check": "Kontrolli vastust", "reset": "Lähtesta vaade", "level": "Juhendatud keemia"})},
        "answer": {"choice": 0, "feedback": _t(
            {"correct_answer": "Covalent bonds share electrons", "explanation": "Each O–H bond in a water molecule is a covalent bond formed by a shared pair of electrons."},
            {"correct_answer": "Kovalentne side jagab elektrone", "explanation": "Iga O–H side veemolekulis on kovalentne side, mille moodustab jagatud elektronpaar."},
        )},
    },
    {
        "source_key": "fl-chem-moles-water", "course_slug": "chemistry-fundamentals", "lesson": "Moles, Masses and Concentration",
        "exercise_type": "mole_calculation", "concepts": ["moles", "formula-mass"], "difficulty_band": 3,
        "prompt": _t("How many moles are in 36.0 g of water (Mr = 18.0)?", "Mitu mooli on 36,0 g vees (Mr = 18,0)?"),
        "public": {"unit": "mol", "ui": _t({"check": "Check calculation", "level": "Guided chemistry", "answer": "Answer"}, {"check": "Kontrolli arvutust", "level": "Juhendatud keemia", "answer": "Vastus"})},
        "answer": {"value": 2.0, "tolerance": 0.01, "feedback": _t(
            {"correct_answer": "2.0 mol", "explanation": "Amount of substance is mass divided by molar mass: 36.0 g ÷ 18.0 g mol⁻¹ = 2.0 mol."},
            {"correct_answer": "2,0 mol", "explanation": "Ainehulk on mass jagatud molaarmassiga: 36,0 g ÷ 18,0 g mol⁻¹ = 2,0 mol."},
        )},
    },
    {
        "source_key": "fl-advanced-vsepr-water", "course_slug": "advanced-chemistry", "lesson": "Orbitals, Spectra and Structure",
        "exercise_type": "molecule_geometry", "concepts": ["vsepr", "lone-pairs"], "difficulty_band": 4,
        "prompt": _t("Rotate the 3D water model. Which molecular shape is predicted by VSEPR?", "Pööra 3D veemudelit. Millist molekulikuju ennustab VSEPR?"),
        "public": {"choices": _t(["Bent", "Linear", "Tetrahedral"], ["Nurgeline", "Lineaarne", "Tetraeedriline"]), "molecule": "water", "scene": "vsepr", "ui": _t({"check": "Check geometry", "reset": "Reset view", "level": "Advanced chemistry"}, {"check": "Kontrolli geomeetriat", "reset": "Lähtesta vaade", "level": "Edasijõudnute keemia"})},
        "answer": {"choice": 0, "feedback": _t(
            {"correct_answer": "Bent", "explanation": "Two bonding pairs and two lone pairs around oxygen give a tetrahedral electron arrangement but a bent molecular shape."},
            {"correct_answer": "Nurgeline", "explanation": "Kaks sidepaari ja kaks üksikut elektronpaari hapniku ümber annavad tetraeedrilise elektronpaigutuse, kuid nurgelise molekulikuju."},
        )},
    },
    {
        "source_key": "fl-advanced-spectra-ethanol", "course_slug": "advanced-chemistry", "lesson": "Spectroscopy and Structure Elucidation",
        "exercise_type": "spectra_choice", "concepts": ["infrared", "functional-groups"], "difficulty_band": 4,
        "prompt": _t("An IR spectrum has a broad O–H absorption. Which functional group is most strongly indicated?", "IR-spektris on lai O–H neeldumisriba. Millisele funktsionaalrühmale see kõige tugevamalt viitab?"),
        "public": {"choices": _t(["Alcohol", "Alkene", "Halogenoalkane"], ["Alkohol", "Alkeen", "Halogenoalkaan"]), "chart": "ir-oh", "ui": _t({"check": "Check interpretation", "level": "Advanced chemistry"}, {"check": "Kontrolli tõlgendust", "level": "Edasijõudnute keemia"})},
        "answer": {"choice": 0, "feedback": _t(
            {"correct_answer": "Alcohol", "explanation": "A broad O–H stretching absorption is characteristic of an alcohol hydroxyl group."},
            {"correct_answer": "Alkohol", "explanation": "Lai O–H valentvõnkumise neeldumisriba on iseloomulik alkoholi hüdroksüülrühmale."},
        )},
    },
    {
        "source_key": "fl-advanced-mechanism-choice", "course_slug": "advanced-chemistry", "lesson": "Mechanisms and Synthesis",
        "exercise_type": "mechanism_choice", "concepts": ["organic-mechanisms", "electron-pairs"], "difficulty_band": 5,
        "prompt": _t("For a nucleophile attacking a positive carbon centre, what does the first curly arrow show?", "Kui nukleofiil ründab positiivset süsinikukeskust, mida näitab esimene kaarnooleke?"),
        "public": {"choices": _t(["A lone pair moving towards carbon", "A proton becoming a neutron", "A bond gaining mass"], ["Üksik elektronpaar liigub süsiniku poole", "Prooton muutub neutroniks", "Side kogub massi"]), "ui": _t({"check": "Check mechanism", "level": "Advanced chemistry"}, {"check": "Kontrolli mehhanismi", "level": "Edasijõudnute keemia"})},
        "answer": {"choice": 0, "feedback": _t(
            {"correct_answer": "A lone pair moving towards carbon", "explanation": "A curly arrow begins at the electron pair being moved and ends where the new bond forms at the electrophilic carbon."},
            {"correct_answer": "Üksik elektronpaar liigub süsiniku poole", "explanation": "Kaarnooleke algab liikuvast elektronpaarist ja lõpeb elektrofiilsel süsinikul, kus moodustub uus side."},
        )},
    },
]


def _english(value):
    if isinstance(value, dict) and set(value).issubset(set(LANGUAGES)):
        return value["en"]
    if isinstance(value, list):
        return [_english(item) for item in value]
    if isinstance(value, dict):
        return {key: _english(item) for key, item in value.items()}
    return value


def _course_translations(course: dict) -> list[tuple[str, str, str | None, str | None]]:
    rows = [("courses", course["slug"], course["title"]["et"], course["description"]["et"])]
    for module in course["modules"]:
        for lesson in module["lessons"]:
            rows.append(("lessons", lesson["title"]["en"], lesson["title"]["et"], lesson["content_md"]["et"]))
    return rows


def public_exercise(exercise: dict, lang: str = "en") -> dict:
    language = lang if lang in LANGUAGES else "en"
    public = deepcopy(exercise["public"])
    for key, value in list(public.items()):
        if isinstance(value, dict) and set(value).issubset(set(LANGUAGES)):
            public[key] = value[language]
    return {
        "source_key": exercise["source_key"], "engine": "chemistry", "exercise_type": exercise["exercise_type"],
        "prompt": exercise["prompt"][language], "concepts": exercise["concepts"],
        "difficulty_band": exercise["difficulty_band"], "cognitive_layer": "skill", **public,
    }


def seed_science_courses(conn, schema: str) -> list[dict]:
    """Install all three curriculum courses without deleting teacher work."""
    owner_id = conn.execute(sa.text(f"SELECT id FROM {schema}.users WHERE lower(email)='kaljuvee@gmail.com' LIMIT 1")).scalar()
    result = []
    lessons_by_course: dict[str, dict[str, int]] = {}
    for source in CATALOG:
        course = _english(source)
        saved = conn.execute(sa.text(f"""
            INSERT INTO {schema}.courses (title, slug, description, category, difficulty, is_published, instructor_id, is_default)
            VALUES (:title, :slug, :description, :category, :difficulty, true, :owner, true)
            ON CONFLICT (slug) DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description,
                category=EXCLUDED.category, difficulty=EXCLUDED.difficulty, is_published=true, is_default=true,
                instructor_id=COALESCE(EXCLUDED.instructor_id, {schema}.courses.instructor_id)
            RETURNING *
        """), {**{key: course[key] for key in ("title", "slug", "description", "category", "difficulty")}, "owner": owner_id}).mappings().one()
        lesson_ids: dict[str, int] = {}
        for module_index, module in enumerate(course["modules"]):
            module_id = conn.execute(sa.text(f"SELECT id FROM {schema}.modules WHERE course_id=:course AND title=:title ORDER BY id LIMIT 1"), {"course": saved["id"], "title": module["title"]}).scalar()
            if module_id:
                conn.execute(sa.text(f"UPDATE {schema}.modules SET order_idx=:order_idx WHERE id=:id"), {"order_idx": module_index, "id": module_id})
            else:
                module_id = conn.execute(sa.text(f"INSERT INTO {schema}.modules (course_id,title,order_idx) VALUES (:course,:title,:order_idx) RETURNING id"), {"course": saved["id"], "title": module["title"], "order_idx": module_index}).scalar_one()
            source_module = source["modules"][module_index]
            conn.execute(sa.text(f"""INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title)
                VALUES ('modules',:id,'et',:title)
                ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title"""),
                {"id": module_id, "title": source_module["title"]["et"]})
            for lesson_index, lesson in enumerate(module["lessons"]):
                lesson_id = conn.execute(sa.text(f"SELECT id FROM {schema}.lessons WHERE module_id=:module AND title=:title ORDER BY id LIMIT 1"), {"module": module_id, "title": lesson["title"]}).scalar()
                params = {"module": module_id, "title": lesson["title"], "content": lesson["content_md"], "duration": lesson["duration_min"], "xp": lesson["xp_reward"], "order_idx": lesson_index}
                if lesson_id:
                    conn.execute(sa.text(f"UPDATE {schema}.lessons SET content_md=:content, content_type='interactive', duration_min=:duration, xp_reward=:xp, order_idx=:order_idx WHERE id=:id"), {**params, "id": lesson_id})
                else:
                    lesson_id = conn.execute(sa.text(f"INSERT INTO {schema}.lessons (module_id,title,content_md,content_type,duration_min,xp_reward,order_idx) VALUES (:module,:title,:content,'interactive',:duration,:xp,:order_idx) RETURNING id"), params).scalar_one()
                lesson_ids[lesson["title"]] = lesson_id
        # English is stored on the base rows; Estonian is stored as entity translations.
        for entity_type, english_title, et_title, et_content in _course_translations(source):
            if entity_type == "courses":
                entity_id = saved["id"]
                conn.execute(sa.text(f"""INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title,description)
                    VALUES ('courses',:id,'et',:title,:description)
                    ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title,description=EXCLUDED.description"""), {"id": entity_id, "title": et_title, "description": et_content})
            else:
                entity_id = lesson_ids[english_title]
                conn.execute(sa.text(f"""INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title,content_md)
                    VALUES ('lessons',:id,'et',:title,:content)
                    ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title,content_md=EXCLUDED.content_md"""), {"id": entity_id, "title": et_title, "content": et_content})
        # Include known legacy lessons in the protected default course. They
        # remain readable for learners with existing progress and receive the
        # same two-mode review contract below.
        existing_lessons = conn.execute(sa.text(f"""
            SELECT l.id, l.title FROM {schema}.lessons l
            JOIN {schema}.modules m ON m.id = l.module_id
            WHERE m.course_id = :course
        """), {"course": saved["id"]}).mappings().all()
        for existing_lesson in existing_lessons:
            lesson_ids.setdefault(existing_lesson["title"], existing_lesson["id"])
        lessons_by_course[source["slug"]] = lesson_ids
        result.append(dict(saved))

    for exercise in EXERCISES:
        public = public_exercise(exercise, "en")
        prompt = public.pop("prompt")
        public.pop("source_key", None)
        public.pop("engine", None)
        public.pop("exercise_type", None)
        public.pop("concepts", None)
        public.pop("difficulty_band", None)
        public.pop("cognitive_layer", None)
        exercise_id = conn.execute(sa.text(f"""
            INSERT INTO {schema}.interactive_exercises (source_key,engine,exercise_type,prompt,concepts,difficulty_band,cognitive_layer,public_payload,answer_payload)
            VALUES (:source_key,'chemistry',:exercise_type,:prompt,CAST(:concepts AS jsonb),:band,'skill',CAST(:public AS jsonb),CAST(:answer AS jsonb))
            ON CONFLICT (source_key) DO UPDATE SET engine='chemistry',exercise_type=EXCLUDED.exercise_type,prompt=EXCLUDED.prompt,
                concepts=EXCLUDED.concepts,difficulty_band=EXCLUDED.difficulty_band,cognitive_layer='skill',public_payload=EXCLUDED.public_payload,answer_payload=EXCLUDED.answer_payload
            RETURNING id
        """), {"source_key": exercise["source_key"], "exercise_type": exercise["exercise_type"], "prompt": prompt, "concepts": json.dumps(exercise["concepts"]), "band": exercise["difficulty_band"], "public": json.dumps(public), "answer": json.dumps(exercise["answer"])}).scalar_one()
        lesson_id = lessons_by_course[exercise["course_slug"]][exercise["lesson"]]
        conn.execute(sa.text(f"""INSERT INTO {schema}.lesson_exercises (lesson_id,exercise_id,order_idx)
            VALUES (:lesson,:exercise,0) ON CONFLICT (lesson_id,exercise_id) DO UPDATE SET order_idx=EXCLUDED.order_idx"""), {"lesson": lesson_id, "exercise": exercise_id})
        localized = public_exercise(exercise, "et")
        localized.pop("source_key", None); localized.pop("engine", None); localized.pop("exercise_type", None)
        localized.pop("concepts", None); localized.pop("difficulty_band", None); localized.pop("cognitive_layer", None)
        et_prompt = localized.pop("prompt")
        conn.execute(sa.text(f"""INSERT INTO {schema}.exercise_translations (exercise_id,language,prompt,public_payload)
            VALUES (:exercise,'et',:prompt,CAST(:public AS jsonb))
            ON CONFLICT (exercise_id,language) DO UPDATE SET prompt=EXCLUDED.prompt,public_payload=EXCLUDED.public_payload"""), {"exercise": exercise_id, "prompt": et_prompt, "public": json.dumps(localized)})

    for review in REVIEW_QUESTIONS:
        lesson_id = lessons_by_course.get(review["course_slug"], {}).get(review["lesson"])
        if not lesson_id:
            # Legacy review rows are intentionally dormant on fresh installs.
            continue
        is_primary = review["course_slug"] == "primary-science"
        en_public = {
            "choices": review["options"]["en"],
            "ui": {
                "check": "Check review",
                "level": "Primary science review" if is_primary else "Chemistry review",
            },
        }
        exercise_id = conn.execute(sa.text(f"""
            INSERT INTO {schema}.interactive_exercises
                (source_key,engine,exercise_type,prompt,concepts,difficulty_band,
                 cognitive_layer,public_payload,answer_payload)
            VALUES (:source_key,'chemistry','multiple_choice',:prompt,
                    CAST(:concepts AS jsonb),:band,'knowledge',
                    CAST(:public AS jsonb),CAST(:answer AS jsonb))
            ON CONFLICT (source_key) DO UPDATE SET
                engine='chemistry',exercise_type='multiple_choice',
                prompt=EXCLUDED.prompt,concepts=EXCLUDED.concepts,
                difficulty_band=EXCLUDED.difficulty_band,
                cognitive_layer='knowledge',public_payload=EXCLUDED.public_payload,
                answer_payload=EXCLUDED.answer_payload
            RETURNING id
        """), {
            "source_key": review["source_key"],
            "prompt": review["question"]["en"],
            "concepts": json.dumps(review["concepts"]),
            "band": review["difficulty_band"],
            "public": json.dumps(en_public),
            "answer": json.dumps({
                "choice": review["correct_index"],
                "feedback": {
                    language: {
                        "correct_answer": review["options"][language][review["correct_index"]],
                        "explanation": review["explanation"][language],
                    }
                    for language in LANGUAGES
                },
            }),
        }).scalar_one()
        conn.execute(sa.text(f"""
            INSERT INTO {schema}.lesson_exercises (lesson_id,exercise_id,order_idx)
            VALUES (:lesson,:exercise,50)
            ON CONFLICT (lesson_id,exercise_id) DO UPDATE SET order_idx=EXCLUDED.order_idx
        """), {"lesson": lesson_id, "exercise": exercise_id})
        et_public = {
            "choices": review["options"]["et"],
            "ui": {
                "check": "Kontrolli kordamist",
                "level": "Loodusõpetuse kordamine" if is_primary else "Keemia kordamine",
            },
        }
        conn.execute(sa.text(f"""
            INSERT INTO {schema}.exercise_translations
                (exercise_id,language,prompt,public_payload)
            VALUES (:exercise,'et',:prompt,CAST(:public AS jsonb))
            ON CONFLICT (exercise_id,language) DO UPDATE SET
                prompt=EXCLUDED.prompt,public_payload=EXCLUDED.public_payload
        """), {
            "exercise": exercise_id,
            "prompt": review["question"]["et"],
            "public": json.dumps(et_public),
        })

        quiz_title_en = f"{review['lesson']} Review"
        quiz_title_et = "Tunni kordamistest"
        quiz_id = conn.execute(sa.text(f"""
            SELECT id FROM {schema}.quizzes
            WHERE lesson_id=:lesson ORDER BY id LIMIT 1
        """), {"lesson": lesson_id}).scalar()
        quiz_params = {
            "lesson": lesson_id, "title": quiz_title_en,
            "threshold": 70, "xp": 20,
        }
        if quiz_id:
            conn.execute(sa.text(f"""
                UPDATE {schema}.quizzes SET title=:title,
                    pass_threshold=:threshold,xp_reward=:xp WHERE id=:id
            """), {**quiz_params, "id": quiz_id})
        else:
            quiz_id = conn.execute(sa.text(f"""
                INSERT INTO {schema}.quizzes
                    (lesson_id,title,pass_threshold,xp_reward)
                VALUES (:lesson,:title,:threshold,:xp) RETURNING id
            """), quiz_params).scalar_one()
        conn.execute(sa.text(f"""
            INSERT INTO {schema}.content_translations
                (entity_type,entity_id,language,title)
            VALUES ('quizzes',:id,'et',:title)
            ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET
                title=EXCLUDED.title
        """), {"id": quiz_id, "title": quiz_title_et})

        question_id = conn.execute(sa.text(f"""
            SELECT id FROM {schema}.quiz_questions
            WHERE quiz_id=:quiz AND order_idx=0 ORDER BY id LIMIT 1
        """), {"quiz": quiz_id}).scalar()
        question_params = {
            "quiz": quiz_id,
            "text": review["question"]["en"],
            "options": json.dumps(review["options"]["en"]),
            "answer": review["options"]["en"][review["correct_index"]],
            "explanation": review["explanation"]["en"],
            "difficulty": review["difficulty_band"],
        }
        if question_id:
            conn.execute(sa.text(f"""
                UPDATE {schema}.quiz_questions SET
                    question_text=:text,question_type='multiple_choice',
                    options=CAST(:options AS jsonb),correct_answer=:answer,
                    explanation=:explanation,difficulty_level=:difficulty,
                    source_type='authored'
                WHERE id=:id
            """), {**question_params, "id": question_id})
        else:
            question_id = conn.execute(sa.text(f"""
                INSERT INTO {schema}.quiz_questions
                    (quiz_id,question_text,question_type,options,correct_answer,
                     explanation,order_idx,difficulty_level,source_type)
                VALUES (:quiz,:text,'multiple_choice',CAST(:options AS jsonb),
                        :answer,:explanation,0,:difficulty,'authored')
                RETURNING id
            """), question_params).scalar_one()
        conn.execute(sa.text(f"""
            INSERT INTO {schema}.content_translations
                (entity_type,entity_id,language,question_text,options,
                 correct_answer,explanation)
            VALUES ('quiz_questions',:id,'et',:text,CAST(:options AS jsonb),
                    :answer,:explanation)
            ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET
                question_text=EXCLUDED.question_text,options=EXCLUDED.options,
                correct_answer=EXCLUDED.correct_answer,
                explanation=EXCLUDED.explanation
        """), {
            "id": question_id,
            "text": review["question"]["et"],
            "options": json.dumps(review["options"]["et"]),
            "answer": review["options"]["et"][review["correct_index"]],
            "explanation": review["explanation"]["et"],
        })
    return result
