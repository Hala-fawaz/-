# 30+ language plan

The UI currently exposes 32 languages.

| # | Language | UI code | NLLB code |
|---|---|---|---|
| 1 | Arabic | ar | arb_Arab |
| 2 | English | en | eng_Latn |
| 3 | French | fr | fra_Latn |
| 4 | Spanish | es | spa_Latn |
| 5 | German | de | deu_Latn |
| 6 | Italian | it | ita_Latn |
| 7 | Portuguese | pt | por_Latn |
| 8 | Turkish | tr | tur_Latn |
| 9 | Urdu | ur | urd_Arab |
| 10 | Persian | fa | pes_Arab |
| 11 | Indonesian | id | ind_Latn |
| 12 | Malay | ms | zsm_Latn |
| 13 | Bengali | bn | ben_Beng |
| 14 | Hindi | hi | hin_Deva |
| 15 | Tamil | ta | tam_Taml |
| 16 | Telugu | te | tel_Telu |
| 17 | Malayalam | ml | mal_Mlym |
| 18 | Punjabi | pa | pan_Guru |
| 19 | Gujarati | gu | guj_Gujr |
| 20 | Marathi | mr | mar_Deva |
| 21 | Russian | ru | rus_Cyrl |
| 22 | Ukrainian | uk | ukr_Cyrl |
| 23 | Chinese | zh | zho_Hans |
| 24 | Japanese | ja | jpn_Jpan |
| 25 | Korean | ko | kor_Hang |
| 26 | Thai | th | tha_Thai |
| 27 | Vietnamese | vi | vie_Latn |
| 28 | Dutch | nl | nld_Latn |
| 29 | Polish | pl | pol_Latn |
| 30 | Swedish | sv | swe_Latn |
| 31 | Greek | el | ell_Grek |
| 32 | Hebrew | he | heb_Hebr |

## Recommendation for the team

Do not translate the original historical corpus permanently into 32 copies.

A better architecture is:

1. Keep the authoritative source in its original language.
2. Retrieve the relevant source passages with RAG.
3. Generate the answer grounded in those passages.
4. Translate the final grounded answer into the user's selected language.
5. Keep the source/reference card attached to the translated answer.

For religious terminology, maintain a controlled glossary so important terms are not translated inconsistently.
