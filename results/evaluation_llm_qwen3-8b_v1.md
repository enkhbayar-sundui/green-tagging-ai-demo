# Evaluation – backend: llm

| Metric | Value |
|---|---|
| n | 16 |
| relevance_accuracy | 0.688 |
| objective_accuracy | 0.5 |
| category_precision | 0.417 |
| category_recall | 0.667 |
| category_f1 | 0.513 |
| errors | 0 |

| ID | Project | Gold | Predicted | Gold categories | Predicted categories | Review |
|---|---|---|---|---|---|---|
| P01 | Solar power plant with battery storage in Dalanzadgad | green | green | RE | RE |  |
| P02 | Нийслэлийн гэр хорооллын айл өрхийн сайжруулсан зуух, д | green | partially_green ✗ | EE;PP | PP |  |
| P03 | Secondary school building No. 5 in Khan-Uul district | not_green | partially_green ✗ |  | GB | yes |
| P04 | School dormitory with rooftop solar and building insula | partially_green | partially_green | EE;RE | EE;GB |  |
| P05 | Expansion of coal-fired thermal power plant unit | harmful | harmful |  | AD;AG;BD;CT;EE;GB;PP;RE;WA;WM |  |
| P06 | Pasture restoration and sustainable grazing in Khangai  | green | green | AD;AG | AG |  |
| P07 | Хот хоорондын авто замын 120 км-ийн шинэчлэл | not_green | partially_green ✗ |  | CT |  |
| P08 | Electric bus fleet for Ulaanbaatar public transport | green | green | CT;PP | CT |  |
| P09 | Flood protection dams and early warning system in Selbe | green | green | AD | AD |  |
| P10 | Green Development Tower office complex | not_green | partially_green ✗ |  | GB | yes |
| P11 | Aimag centre wastewater treatment plant | green | green | WA | WA |  |
| P12 | Мод тарих "Тэрбум мод" үндэсний хөдөлгөөний ойжуулалт | green | green | AG;WA | AG |  |
| P13 | Waste sorting and recycling facility | green | green | WM | WM |  |
| P14 | Soum hospital renovation | not_green | not_green |  |  | yes |
| P15 | New coal mine access railway | harmful | not_green ✗ |  |  |  |
| P16 | Protected area management and wildlife monitoring in Kh | green | green | BD | BD |  |
