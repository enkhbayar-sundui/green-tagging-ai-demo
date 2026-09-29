"""Green-tagging criteria used by the demo.

The categories are ILLUSTRATIVE and adapted from the structure of the Mongolia
Green Taxonomy (2019) and common climate budget tagging practice (mitigation /
adaptation relevance). In a real deployment they would be replaced by the
official criteria issued by the Ministry of Finance for budget green tagging.
Each category carries English and Mongolian keywords (used by the offline
baseline) and the national / global frameworks it maps to.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Category:
    code: str
    name: str
    name_mn: str
    objective: str  # mitigation | adaptation | both
    keywords: tuple[str, ...]
    sdgs: tuple[int, ...] = field(default_factory=tuple)
    frameworks: tuple[str, ...] = field(default_factory=tuple)


CATEGORIES: list[Category] = [
    Category("RE", "Renewable energy", "Сэргээгдэх эрчим хүч", "mitigation",
             ("solar", "wind", "photovoltaic", "hydropower", "renewable", "battery storage",
              "нар", "салхи", "сэргээгдэх", "усан цахилгаан", "хуримтлуур"),
             (7, 13), ("NDC: energy sector", "Vision 2050")),
    Category("EE", "Energy efficiency", "Эрчим хүчний хэмнэлт", "mitigation",
             ("energy efficiency", "insulation", "retrofit", "led lighting", "heat loss", "district heating upgrade",
              "эрчим хүчний хэмнэлт", "дулаалга", "дулааны алдагдал", "led гэрэлтүүлэг"),
             (7, 13), ("NDC: energy/buildings",)),
    Category("GB", "Green buildings", "Ногоон барилга", "mitigation",
             ("green building", "passive house", "energy-efficient building", "edge certification",
              "ногоон барилга", "эрчим хүчний хэмнэлттэй барилга"),
             (11, 13), ("NDC: buildings",)),
    Category("CT", "Clean transport", "Цэвэр тээвэр", "mitigation",
             ("electric bus", "electric vehicle", "bus rapid transit", "cycling", "metro", "rail electrification",
              "цахилгаан автобус", "цахилгаан тээвэр", "дугуйн зам", "нийтийн тээвэр"),
             (11, 13), ("NDC: transport",)),
    Category("PP", "Pollution prevention and control", "Бохирдлоос урьдчилан сэргийлэх", "mitigation",
             ("air pollution", "clean stove", "improved stove", "emission reduction", "ger district heating",
              "агаарын бохирдол", "сайжруулсан зуух", "утаа", "ялгарал бууруулах"),
             (3, 11, 13), ("NDC: energy", "National Program on Air Pollution")),
    Category("WA", "Sustainable water and wastewater", "Ус, бохир усны тогтвортой менежмент", "adaptation",
             ("wastewater treatment", "water saving", "drip irrigation", "water reuse", "groundwater recharge",
              "бохир ус цэвэрлэх", "ус хэмнэх", "дусал услалт", "усны нөөц"),
             (6, 13), ("NAP: water", "NDC: adaptation")),
    Category("WM", "Waste management and circular economy", "Хог хаягдлын менежмент", "mitigation",
             ("recycling", "composting", "landfill gas", "waste sorting", "circular",
              "дахин боловсруулах", "хог ангилах", "бордоо", "хогийн цэг"),
             (11, 12), ("NDC: waste",)),
    Category("AG", "Sustainable agriculture, pasture and forestry", "Тогтвортой хөдөө аж ахуй, бэлчээр, ойн аж ахуй", "both",
             ("pasture restoration", "rangeland", "reforestation", "afforestation", "sustainable grazing",
              "tree planting", "soil conservation", "бэлчээр", "ой сэргээх", "мод тарих", "ногоон хэрэм", "хөрс хамгаалах"),
             (2, 13, 15), ("NDC: AFOLU", "NBSAP", "NAP: agriculture", "One Billion Trees")),
    Category("AD", "Climate change adaptation and resilience", "Уур амьсгалын өөрчлөлтөд дасан зохицох", "adaptation",
             ("early warning", "flood protection", "drought", "dzud", "climate resilient", "disaster risk",
              "эрт сэрэмжлүүлэг", "үер", "ган", "зуд", "гамшгийн эрсдэл", "дасан зохицох"),
             (1, 11, 13), ("NAP", "NDC: adaptation", "Sendai Framework")),
    Category("BD", "Biodiversity and ecosystem protection", "Биологийн төрөл зүйл, экосистем хамгаалах", "adaptation",
             ("protected area", "biodiversity", "wildlife", "wetland", "ecosystem restoration",
              "тусгай хамгаалалттай", "биологийн олон янз", "зэрлэг амьтан", "намгархаг", "экосистем"),
             (14, 15), ("NBSAP", "Kunming-Montreal GBF")),
]

# Activities that indicate environmental harm (negative / "brown" signal).
HARMFUL_KEYWORDS: tuple[str, ...] = (
    "coal-fired", "coal power", "coal mine", "new coal", "oil refinery", "diesel generator",
    "нүүрсний цахилгаан", "нүүрсний уурхай", "дизель генератор", "нүүрс олборлох",
)

BY_CODE = {c.code: c for c in CATEGORIES}

RELEVANCE_LEVELS = ("green", "partially_green", "not_green", "harmful")
