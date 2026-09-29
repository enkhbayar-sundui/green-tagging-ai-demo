"""Streamlit demo UI for non-technical reviewers (Mongolian by default).

    streamlit run app.py
"""
import os

import pandas as pd
import streamlit as st

from greentag.evaluate import ROOT, load
from greentag.schema import ProjectProposal
from greentag.tagger import llm_available, tag
from greentag.taxonomy import BY_CODE

T = {
    "Mongolian": {
        "title": "🌱 Улсын хөрөнгө оруулалтын төслийн ногоон тэмдэглэгээ – AI туслах",
        "caption": "Прототип · зохиомол өгөгдөл · эцсийн шийдвэрийг хянагч албан хаагч гаргана",
        "settings": "Тохиргоо", "engine": "Хөдөлгүүр", "llm": "LLM (бүтэцтэй гаралт)",
        "rules": "Түлхүүр үгийн шалгалт (offline)", "provider": "Үйлчилгээ",
        "no_llm": "LLM алга (API түлхүүр байхгүй эсвэл Ollama ажиллаагүй) – түлхүүр үгийн шалгалт ашиглана.",
        "tab1": "Нэг төсөл", "tab2": "Олон төсөл (CSV)", "sample": "Жишээ төсөл сонгох",
        "own": "— өөрөө бичих —", "ptitle": "Төслийн нэр", "ministry": "Яам / байгууллага",
        "desc": "Тайлбар / үйл ажиллагаа", "obj": "Зорилго", "loc": "Байршил",
        "budget": "Төсөв (сая төгрөг)", "run": "Ангилах", "busy": "Шинжилж байна…",
        "rel": "Ногоон байдал", "cobj": "Уур амьсгалын зорилт", "share": "Төсвийн ногоон хувь",
        "conf": "Итгэлцүүр", "review": "⚠️ Хүн шалгах шаардлагатай", "cats": "Ангилал",
        "sdg": "ТХЗ (SDG)", "fw": "Бодлогын баримт бичиг", "evidence": "Төслийн баримтаас иш татсан нь",
        "json": "Бүтэцтэй гаралт (JSON)", "used": "Ашигласан хөдөлгүүр", "none": "байхгүй",
        "csv_help": "Дараах баганатай CSV файл оруулна: project_id, title, ministry, budget_mnt_million, "
                    "description, objectives, location.",
        "file": "CSV файл", "run_all": "Бүгдийг ангилах", "download": "Үр дүн татах (CSV)",
        "relv": {"green": "ногоон", "partially_green": "хэсэгчлэн ногоон", "not_green": "ногоон биш",
                 "harmful": "хор хөнөөлтэй"},
        "objv": {"mitigation": "бууруулах", "adaptation": "дасан зохицох", "both": "хоёулаа", "none": "үгүй"},
    },
    "English": {
        "title": "🌱 AI-assisted green tagging of public investment projects",
        "caption": "Prototype · synthetic data · final decision always rests with the reviewing officer",
        "settings": "Settings", "engine": "Engine", "llm": "LLM (structured output)",
        "rules": "Keyword baseline (offline)", "provider": "Provider",
        "no_llm": "No LLM available (no API key, or Ollama not running) – using the keyword baseline.",
        "tab1": "Single proposal", "tab2": "Batch (CSV)", "sample": "Load a sample proposal",
        "own": "— write your own —", "ptitle": "Project title", "ministry": "Ministry / agency",
        "desc": "Description / activities", "obj": "Objectives", "loc": "Location",
        "budget": "Budget (MNT million)", "run": "Tag proposal", "busy": "Analysing…",
        "rel": "Green relevance", "cobj": "Climate objective", "share": "Green share of budget",
        "conf": "Confidence", "review": "⚠️ Flagged for human review", "cats": "Categories",
        "sdg": "SDGs", "fw": "Frameworks", "evidence": "Evidence from the proposal",
        "json": "Structured output (JSON)", "used": "Engine used", "none": "none",
        "csv_help": "Upload a CSV with columns: project_id, title, ministry, budget_mnt_million, description, "
                    "objectives, location.",
        "file": "CSV file", "run_all": "Tag all", "download": "Download results (CSV)",
        "relv": {"green": "green", "partially_green": "partially green", "not_green": "not green",
                 "harmful": "harmful"},
        "objv": {"mitigation": "mitigation", "adaptation": "adaptation", "both": "both", "none": "none"},
    },
}

st.set_page_config(page_title="Green Tagging AI", page_icon="🌱", layout="wide")

with st.sidebar:
    lang = st.radio("Хэл / Language", ["Mongolian", "English"],
                    format_func=lambda x: "Монгол" if x == "Mongolian" else "English")
    L = T[lang]
    st.header(L["settings"])
    backend = st.radio(L["engine"], ["llm", "rules"], index=0 if llm_available() else 1,
                       format_func=lambda b: L["llm"] if b == "llm" else L["rules"])
    if backend == "llm" and not llm_available():
        st.warning(L["no_llm"])
        backend = "rules"
    if backend == "llm":
        st.caption(f"{L['provider']}: {os.getenv('GREENTAG_PROVIDER', 'anthropic')} · "
                   f"{os.getenv('GREENTAG_MODEL', '')}")

st.title(L["title"])
st.caption(L["caption"])
tab1, tab2 = st.tabs([L["tab1"], L["tab2"]])
samples = {p.title: p for p, _ in load(ROOT / "data" / "sample_projects.csv")}


def cat_label(c):
    cat = BY_CODE[c]
    return f"{c} – {cat.name_mn if lang == 'Mongolian' else cat.name}"


with tab1:
    choice = st.selectbox(L["sample"], [L["own"]] + list(samples))
    base = samples.get(choice) or ProjectProposal(project_id="NEW", title="", description="")
    c1, c2 = st.columns(2)
    title = c1.text_input(L["ptitle"], base.title)
    ministry = c2.text_input(L["ministry"], base.ministry)
    desc = st.text_area(L["desc"], base.description, height=120)
    obj = st.text_area(L["obj"], base.objectives, height=70)
    c3, c4 = st.columns(2)
    loc = c3.text_input(L["loc"], base.location)
    budget = c4.number_input(L["budget"], value=float(base.budget_mnt_million or 0))
    if st.button(L["run"], type="primary", disabled=not desc.strip()):
        p = ProjectProposal(project_id=base.project_id, title=title, ministry=ministry, description=desc,
                            objectives=obj, location=loc, budget_mnt_million=budget)
        with st.spinner(L["busy"]):
            try:
                t, used = tag(p, backend=backend, lang=lang)
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")
                st.stop()
        icon = {"green": "🟢", "partially_green": "🟡", "not_green": "⚪", "harmful": "🔴"}[t.green_relevance]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(L["rel"], f"{icon} {L['relv'][t.green_relevance]}")
        m2.metric(L["cobj"], L["objv"][t.climate_objective])
        m3.metric(L["share"], f"{t.green_share_pct}%")
        m4.metric(L["conf"], f"{t.confidence:.0%}")
        if t.needs_human_review:
            st.warning(L["review"])
        st.markdown(f"**{L['cats']}:** " + (", ".join(cat_label(c) for c in t.taxonomy_categories) or L["none"]))
        st.markdown(f"**{L['sdg']}:** " + (", ".join(map(str, t.sdg_goals)) or "–") +
                    f" · **{L['fw']}:** " + (", ".join(t.frameworks) or "–"))
        st.info(t.rationale)
        if t.evidence:
            st.markdown(f"**{L['evidence']}:** " + " · ".join(f"“{e}”" for e in t.evidence))
        with st.expander(L["json"]):
            st.json(t.model_dump())
        st.caption(f"{L['used']}: {used}")

with tab2:
    st.write(L["csv_help"])
    up = st.file_uploader(L["file"], type="csv")
    if up and st.button(L["run_all"]):
        df = pd.read_csv(up).fillna("")
        out = []
        bar = st.progress(0.0)
        for i, r in df.iterrows():
            p = ProjectProposal(project_id=str(r["project_id"]), title=r["title"], ministry=r.get("ministry", ""),
                                description=r["description"], objectives=r.get("objectives", ""),
                                location=r.get("location", ""),
                                budget_mnt_million=float(r.get("budget_mnt_million") or 0))
            try:
                t, _ = tag(p, backend=backend, lang=lang)
                out.append({"project_id": p.project_id, "title": p.title, **t.model_dump(), "error": ""})
            except Exception as e:  # one slow/failed proposal must not stop the batch
                out.append({"project_id": p.project_id, "title": p.title, "error": f"{type(e).__name__}: {e}"})
            bar.progress((i + 1) / len(df), text=f"{i + 1}/{len(df)}")
        res = pd.DataFrame(out)
        st.dataframe(res, use_container_width=True)
        st.download_button(L["download"], res.to_csv(index=False).encode("utf-8-sig"),
                           "green_tagging_results.csv", "text/csv")
