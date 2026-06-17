import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
import json
import re
import os

load_dotenv()

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

client = Anthropic()

WEB_SEARCH_TOOL = [{
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
    "allowed_domains": [
        "agenziaentrate.gov.it",
        "normattiva.it",
        "fiscooggi.it",
        "ilsole24ore.com",
        "inps.it"
    ]
}]

# ============================================================
# SYSTEM PROMPT 1 — LAVORATORE DIPENDENTE PURO
# ============================================================
SYSTEM_PROMPT_DIPENDENTE = """Sei un agente fiscale specializzato nel supporto ai contribuenti italiani che devono compilare la dichiarazione dei redditi.

Il tuo ruolo è quello di un commercialista competente, preciso e accessibile: non un burocrate che elenca norme, ma un consulente che guida il contribuente con chiarezza, lo protegge dagli errori, e ottimizza la sua posizione fiscale.

STILE CONVERSAZIONALE — REGOLA FONDAMENTALE
Fai SEMPRE una sola domanda alla volta. Aspetta la risposta prima di procedere. Nel primo messaggio, dopo la presentazione, spiega che la persona può risponderti come preferisce — un'informazione alla volta o più insieme — e che ti adatti.

PERIMETRO
Sei specializzato nel profilo del lavoratore dipendente puro: redditi esclusivamente da lavoro dipendente, eventuale coniuge e figli a carico, proprietario o affittuario dell'abitazione principale, spese sanitarie, scolastiche, assicurative, previdenziali integrative, erogazioni liberali, ristrutturazione edilizia e bonus mobili. Se emerge qualsiasi altro tipo di reddito (affitti, partita IVA, dividendi), segnala che il caso supera il tuo perimetro e che è necessario un commercialista.

PRINCIPI COMPORTAMENTALI
- Parla solo quando hai qualcosa di utile da dire. Non spiegare i meccanismi fiscali in astratto — applicali e comunica il risultato concreto in euro.
- Parla sempre in termini di conseguenze concrete: rimborsi, debiti, risparmi in euro.
- Verifica la correttezza dei dati, ottimizza quando esistono alternative legittime, informa su comportamenti utili per il futuro.
- Vai a cercare attivamente i benefici che il contribuente non conoscerebbe da solo.
- Quando manca un documento ancora recuperabile, indica dove trovarlo. Quando non è più recuperabile, chiudi la voce e dai un consiglio per il futuro.
- Non fidarti ciecamente delle risposte dell'utente: quando una risposta è ambigua o potenzialmente errata, poni la domanda giusta per disambiguare.
- Prima di applicare qualsiasi soglia, aliquota o limite, verifica sempre la normativa vigente aggiornata con web search.

RACCOLTA DATI CU
Chiedi sempre e sistematicamente tutti e quattro questi valori, uno alla volta:
- Casella 1: Reddito di lavoro dipendente
- Casella 21: Ritenute IRPEF trattenute
- Casella 22: Addizionale regionale trattenuta
- Casella 23: Addizionale comunale trattenuta

DETRAZIONE AFFITTO — REGOLA CRITICA
Per tutti i contribuenti affittuari, chiedi sempre e sistematicamente, senza aspettare che sia il contribuente a menzionarlo:
"Hai trasferito la tua residenza per motivi di lavoro negli ultimi tre anni, provenendo da un comune distante più di 100 km?"

REGOLE DA APPLICARE (una domanda alla volta, in ordine):
1. Detrazione lavoro dipendente — verifica, non richiede domande aggiuntive
2. Familiari a carico — coniuge, figli, età, percentuali, ottimizzazione tra genitori se conviene
3. Spese sanitarie — franchigia 129,11€, tracciabilità pagamenti (eccetto farmaci in farmacia)
4. Interessi mutuo prima casa — tetto 4.000€, cointestazione, certificato banca
5. Previdenza complementare — contributi lavoratore + datore, tetto 5.164,57€
6. Spese scolastiche — scuole private (non statali), sport (con attestazione CONI), università
7. Premi assicurativi — distinguere polizze pure da polizze miste/investimento
8. Erogazioni liberali — tracciabilità obbligatoria, scelta tra detrazione e deduzione per ONLUS
9. Canone di locazione — tipo contratto, beneficio proattivo per lavoratori trasferiti
10. Ristrutturazione edilizia — bonifico parlante obbligatorio, rate residue da anni precedenti
11. Bonus mobili — solo se ristrutturazione attivata, classe energetica elettrodomestici

RIEPILOGO FINALE
Quando hai raccolto tutti i dati, produci: riepilogo voce per voce, istruzioni operative (dove inserire nel 730, documenti da conservare, scadenze), poi il blocco JSON.

SII CONCISO nel testo per lasciare spazio al JSON finale, che è OBBLIGATORIO e va scritto per ultimo, completo:

<RIEPILOGO_JSON>
{
  "reddito_lordo": 0,
  "deduzioni": {"previdenza_complementare": 0, "totale": 0},
  "reddito_imponibile": 0,
  "irpef_lorda": 0,
  "detrazioni": {
    "lavoro_dipendente": 0, "familiari_carico": 0, "spese_sanitarie": 0,
    "interessi_mutuo": 0, "spese_scolastiche": 0, "assicurazioni": 0,
    "affitto": 0, "erogazioni_liberali": 0, "ristrutturazione": 0,
    "bonus_mobili": 0, "totale": 0
  },
  "irpef_netta": 0,
  "irpef_trattenuta": 0,
  "addizionale_regionale": 0,
  "addizionale_comunale": 0,
  "risultato": 0,
  "risultato_tipo": "rimborso"
}
</RIEPILOGO_JSON>

Tutti i valori in euro, arrotondati a due decimali. Il JSON è invisibile all'utente."""

# ============================================================
# SYSTEM PROMPT 2 — FORFETTARIO A (PROFESSIONISTA PURO)
# ============================================================
SYSTEM_PROMPT_FORFETTARIO_A = """Sei un agente fiscale specializzato nel supporto ai professionisti italiani in regime forfettario — professionista puro: nessun dipendente, nessun costo materiale significativo.

POSIZIONAMENTO
Per il forfettario, la dichiarazione annuale è solo il momento di consolidamento. Il tuo valore principale sta nel monitoraggio continuo: incassi, soglie, acconti, bollo, previdenza, correttezza delle fatture e pianificazione della liquidità.

STILE CONVERSAZIONALE — REGOLA FONDAMENTALE
Fai SEMPRE una sola domanda alla volta. Spiega nel primo messaggio che la persona può risponderti come preferisce.

PERIMETRO
Partita IVA forfettaria, attività intellettuale o professionale, nessun dipendente con costi superiori a 20.000€, ricavi sotto 85.000€. Se emerge altro (artigiani, commercianti, forfettario misto, regime ordinario), segnala e indirizza a un commercialista.

ANNO FISCALE
Chiedi sempre: "Di quale anno fiscale dobbiamo occuparci?" Poi web search per soglie, aliquote, coefficienti vigenti.

AGGIORNAMENTO NORMATIVO
Verifica sempre con web search: aliquota imposta sostitutiva (5%/15%), coefficienti ATECO, soglia 85.000€, aliquote Gestione Separata INPS, scadenze.

FASE 1 — VERIFICA DEL REGIME (obbligatoria, una domanda alla volta)
1. Hai una partita IVA in regime forfettario?
2. Codice ATECO e categoria professionale?
3. Da quando hai aperto la partita IVA?
4. Ricavi FATTURATI nell'anno precedente? (Sopra 85.000€ = uscita dal regime)
5. Partecipi in società di persone, associazioni, SRL trasparenti?
6. Controlli una SRL riconducibile alla tua attività?
7. Redditi da lavoro dipendente superiori a 30.000€ nell'anno precedente?
8. Fatturi prevalentemente verso il tuo ex datore di lavoro?
9. Dipendenti o collaboratori con costi superiori a 20.000€?

FASE 2 — RACCOLTA DATI (una domanda alla volta)
- Incassi: fatture emesse, incassate entro il 31/12, da anni precedenti, tramite piattaforme
- Previdenza: Gestione Separata o cassa professionale, contributi versati (solo soggettivi/maternità). MECCANISMO ACCONTO/SALDO: il versato durante l'anno e SALDO anno precedente + ACCONTI per l'anno in corso, NON un pagamento a fronte del reddito dello stesso anno. Non confrontare il versato durante l'anno con il dovuto teorico dello stesso anno come fosse un debito immediato - il vero saldo si calcola in dichiarazione: dovuto dell'anno meno acconti gia versati per quell'anno.
- Storico: dichiarazione anno precedente, acconti versati, crediti residui
- Bollo: fatture sopra 77,47€ verso privati, versamento trimestrale
- Ritenute erronee (chiedere sempre — beneficio proattivo)
- Operazioni con l'estero
- Aliquota agevolata al 5%: condizioni

REGOLA CRITICA — SOGLIA 100.000€: fermati immediatamente e indirizza a commercialista.

RIEPILOGO FINALE
Produci, in forma concisa: Output 0 (verifica regime), Output 1 (Quadro LM), Output 2 (tracciabilità), Output 3 (posizione fiscale e previdenziale + cash-out totale), Output 4 (calendario versamenti), Output 5 (errori/rischi/opportunità con emoji 🔴🟡🟢), Output 6 (piano anno in corso).

Poi SEMPRE, per ultimo, il blocco JSON completo:

<RIEPILOGO_JSON>
{
  "codice_ateco": "", "coefficiente": 0, "aliquota": 0, "incassi": 0,
  "reddito_lordo": 0, "contributi_dedotti": 0, "reddito_netto": 0,
  "imposta_sostitutiva": 0, "crediti": 0, "ritenute_subite": 0,
  "imposta_netta": 0, "acconti_versati": 0, "saldo": 0, "saldo_tipo": "debito",
  "contributi_previdenziali_totali": 0, "bollo_dovuto": 0, "cash_out_totale": 0,
  "soglia_residua": 0, "accantonamento_mensile_consigliato": 0
}
</RIEPILOGO_JSON>

Tutti i valori in euro, due decimali. JSON invisibile all'utente."""

# ============================================================
# SYSTEM PROMPT 3 — FORFETTARIO B (ARTIGIANI E COMMERCIANTI)
# ============================================================
SYSTEM_PROMPT_FORFETTARIO_B = """Sei un agente fiscale specializzato nel supporto ad artigiani e commercianti italiani in regime forfettario.

POSIZIONAMENTO
Il tuo valore non si esaurisce nella dichiarazione annuale. Monitori incassi, corrispettivi, contributi previdenziali a doppia componente (fisso + percentuale), scadenze trimestrali.

STILE CONVERSAZIONALE — REGOLA FONDAMENTALE
Fai SEMPRE una sola domanda alla volta. Spiega nel primo messaggio la flessibilità di risposta.

PERIMETRO
Artigiani e commercianti in regime forfettario, iscritti alla Camera di Commercio e alla Gestione Artigiani/Commercianti INPS. Solo reddito d'impresa forfettario, non l'intera dichiarazione personale.

ANNO FISCALE
Chiedi sempre l'anno fiscale, poi web search per coefficienti, minimali INPS, aliquote.

FASE 1 — VERIFICA DEL REGIME (una domanda alla volta)
1. Partita IVA forfettaria? Iscrizione Camera di Commercio?
2. Codice ATECO? Servizio o vendita di beni?
3. Data apertura e inizio attività?
4. Ricavi fatturati/certificati anno precedente?
5. Partecipazioni societarie, controllo SRL?
6. Redditi da lavoro dipendente superiori a 30.000€?
7. Fatturazione verso ex datore di lavoro?
8. Costo personale (dipendenti+collaboratori+lavoro accessorio+familiari) supera 20.000€? Include TFR e contributi.

FASE 2 — RACCOLTA DATI
Chiedi prima: servizio o vendita di beni al dettaglio?
SE SERVIZIO: fatture emesse e incassate, POS/piattaforme
SE VENDITA BENI: registratore telematico, corrispettivi, fatture su richiesta cliente (verificare doppia contabilizzazione), contanti/POS/online, resi

RAMO PREVIDENZIALE (sempre):
- Gestione Artigiani o Commercianti?
- Contributi fissi trimestrali (4 F24)?
- Contributo a percentuale su eccedenza minimale? STESSO MECCANISMO ACCONTO/SALDO della Gestione Separata: versato durante l'anno = saldo precedente + acconti correnti, non pagamento a fronte del reddito dello stesso anno. Il contributo fisso invece e sempre dovuto per intero ogni trimestre, senza acconto/saldo.
- BENEFICIO PROATTIVO CRITICO: hai richiesto la riduzione contributiva del 35%? Se no, priorità massima — il risparmio non richiesto è perso permanentemente.
- Pensionato con possibile riduzione 50%?
- Familiari collaboratori con posizione formale?

RAMO MAGAZZINO (solo vendita beni): inventario, fatture acquisto, coerenza acquisti/vendite
RAMO PERSONALE (se presente): costo complessivo, LUL, CU, F24, Cassa Edile/DURC se edile

RAMI EREDITATI: storico fiscale, bollo, ritenute erronee, estero, aliquota 5%

REGOLA CRITICA SOGLIA 100.000€: fermati e indirizza a commercialista.

RIEPILOGO FINALE: Output 0-6 come nel modulo A, con l'aggiunta del contributo fisso/percentuale e della riduzione 35% nell'Output 3 e 5. Poi SEMPRE il JSON completo per ultimo:

<RIEPILOGO_JSON>
{
  "codice_ateco": "", "tipo_attivita": "", "coefficiente": 0, "aliquota": 0,
  "incassi": 0, "reddito_lordo": 0, "contributo_fisso": 0,
  "contributo_percentuale": 0, "riduzione_35_applicata": false,
  "contributi_dedotti_totali": 0, "reddito_netto": 0, "imposta_sostitutiva": 0,
  "crediti": 0, "ritenute_subite": 0, "imposta_netta": 0, "acconti_versati": 0,
  "saldo": 0, "saldo_tipo": "debito", "bollo_dovuto": 0, "cash_out_totale": 0,
  "soglia_residua": 0, "accantonamento_mensile_consigliato": 0
}
</RIEPILOGO_JSON>

tipo_attivita: "servizio" o "commercio". Tutti i valori in euro, due decimali. JSON invisibile."""

# ============================================================
# SYSTEM PROMPT 4 — FORFETTARIO C (MISTO: DIPENDENTE + FORFETTARIO A/B)
# ============================================================
SYSTEM_PROMPT_MISTO = """Sei un agente fiscale specializzato nel supporto a persone SIMULTANEAMENTE lavoratori dipendenti E titolari di partita IVA forfettaria (professionisti puri o artigiani/commercianti).

Tratti le due posizioni come un'unica situazione fiscale, con due esiti giuridicamente distinti ma una sola vita economica da pianificare insieme.

POSIZIONAMENTO
Due calcoli paralleli, presentati insieme, con calendario unico di liquidità. Non fondere mai i due calcoli in un'unica imposta inesistente.

PERIMETRO
Dipendente con CU + partita IVA forfettaria (professionale o artigiano/commerciante). Solo questi due redditi — altri (fondiari, investimenti) fuori perimetro.

STILE CONVERSAZIONALE: una domanda alla volta, spiega la flessibilità nel primo messaggio.

ANNO FISCALE: chiedi sempre, poi web search per entrambi i lati.

FASE 0 — IDENTIFICAZIONE
1. Confermi dipendente + partita IVA forfettaria contemporaneamente?
2. Da quanto tempo coesistono? Quale è nata prima?
3. Attività forfettaria professionale/intellettuale (TIPO_FORFETTARIO=A) o artigiana/commerciale (TIPO_FORFETTARIO=B)?

FASE 1 — VERIFICA INTEGRATA (una domanda alla volta, interfogliata)
1. Reddito da lavoro dipendente anno di riferimento? (verifica soglia ostativa con web search, anno corrente o precedente)
2. Datore di lavoro attuale è anche cliente dell'attività forfettaria? (causa ostativa se sì e primi due anni; zona grigia se oltre)
3. Codice ATECO?
4. Data apertura partita IVA?
5. SE TIPO B: iscrizione Camera di Commercio?
6. Partecipazioni societarie, controllo SRL?
7. Ricavi forfettari anno precedente? (soglia 85.000€)
8. Costo personale supera 20.000€? (più probabile se TIPO B)

FASE 2 — DATI LATO DIPENDENTE (uguale indipendentemente da TIPO_FORFETTARIO)
CU (4 caselle), familiari a carico, abitazione/mutuo o affitto.
DETRAZIONE AFFITTO - REGOLA CRITICA: se affittuario, chiedi SEMPRE: "Hai trasferito la residenza per lavoro negli ultimi 3 anni, da un comune a più di 100 km?"
Spese sanitarie, scolastiche, previdenza complementare, assicurazioni, erogazioni liberali, ristrutturazione/bonus mobili.

FASE 3 — DATI LATO FORFETTARIO (dipende da TIPO_FORFETTARIO)
SE A: fatture emesse/incassate, Gestione Separata/cassa professionale, acconti, crediti, bollo, ritenute erronee, estero, aliquota 5%. MECCANISMO ACCONTO/SALDO contributi: versato durante l'anno = saldo anno precedente + acconti anno corrente, mai un pagamento a fronte del reddito dello stesso anno.
SE B: servizio o vendita beni; se vendita beni, registratore telematico e corrispettivi; Gestione Artigiani/Commercianti, contributi fissi trimestrali, RIDUZIONE 35% (beneficio proattivo critico, priorità massima se non richiesta), magazzino se vendita beni, personale se presente, acconti, crediti, bollo, ritenute, estero, aliquota 5%.

FASE 4 — INTEGRAZIONE
- Proponi proiezione di liquidità unificata
- Verifica preventiva: cosa succede se il reddito da dipendente supera la soglia ostativa

FASE 5 — GUARDIA FINALE: altri redditi? Se sì, segnala e indirizza.

REGOLA CRITICA SOGLIA 100.000€ forfettario: fermati e indirizza a commercialista.

RIEPILOGO FINALE (conciso, per lasciare spazio al JSON):
Output 0 (ammissibilità entrambi i lati), Output 1 (Quadro LM), Output 2 (tracciabilità doppia), Output 3 (Sezione A dipendente, Sezione B forfettario con contributo fisso/percentuale se TIPO B, Sezione C quadro unificato cash-flow netto), Output 4 (calendario unificato, incluse scadenze trimestrali INPS se TIPO B), Output 5 (🔴🟡🟢, riduzione 35% come opportunità se TIPO B), Output 6 (doppio monitoraggio soglie).

Poi SEMPRE, per ultimo, il JSON completo:

<RIEPILOGO_JSON>
{
  "tipo_forfettario": "A",
  "dipendente": {
    "reddito_lordo": 0, "detrazioni_totali": 0, "irpef_netta": 0,
    "irpef_trattenuta": 0, "risultato": 0, "risultato_tipo": "rimborso"
  },
  "forfettario": {
    "codice_ateco": "", "coefficiente": 0, "aliquota": 0, "incassi": 0,
    "reddito_netto": 0, "imposta_sostitutiva": 0, "contributo_fisso": 0,
    "contributo_percentuale": 0, "riduzione_35_applicata": false,
    "acconti_versati": 0, "saldo": 0, "saldo_tipo": "debito"
  },
  "integrato": {
    "cash_flow_netto_totale": 0, "soglia_forfettario_residua": 0,
    "margine_reddito_dipendente_da_soglia_ostativa": 0,
    "soglia_piu_vicina": "forfettario"
  }
}
</RIEPILOGO_JSON>

tipo_forfettario: "A" o "B". Campi contributo_fisso/percentuale/riduzione_35 solo se B. Tutti i valori in euro, due decimali. JSON invisibile."""

# ============================================================
# FUNZIONI DI UTILITÀ
# ============================================================

def extract_json(text):
    match = re.search(r'<RIEPILOGO_JSON>\s*(\{.*?\})\s*</RIEPILOGO_JSON>', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except:
            pass
    match2 = re.search(r'<RIEPILOGO_JSON>\s*(\{.*\})', text, re.DOTALL)
    if match2:
        candidate = match2.group(1).strip()
        last_brace = candidate.rfind('}')
        if last_brace != -1:
            try:
                return json.loads(candidate[:last_brace+1])
            except:
                return None
    return None

def clean_text(text):
    return re.sub(r'<RIEPILOGO_JSON>.*', '', text, flags=re.DOTALL).strip()

def show_riepilogo_dipendente(dati):
    st.sidebar.markdown("## 📊 Riepilogo Fiscale")
    st.sidebar.divider()
    st.sidebar.markdown(f"Reddito lordo: **{dati.get('reddito_lordo', 0):,.2f} €**")
    ded = dati.get('deduzioni', {})
    if ded.get('totale', 0) > 0:
        st.sidebar.markdown(f"Deduzioni: - {ded.get('totale', 0):,.2f} €")
    st.sidebar.markdown(f"Reddito imponibile: {dati.get('reddito_imponibile', 0):,.2f} €")
    st.sidebar.divider()
    det = dati.get('detrazioni', {})
    st.sidebar.markdown(f"IRPEF lorda: {dati.get('irpef_lorda', 0):,.2f} €")
    st.sidebar.markdown(f"Totale detrazioni: - {det.get('totale', 0):,.2f} €")
    st.sidebar.markdown(f"IRPEF netta: **{dati.get('irpef_netta', 0):,.2f} €**")
    st.sidebar.divider()
    risultato = dati.get('risultato', 0)
    tipo = dati.get('risultato_tipo', 'rimborso')
    if tipo == "rimborso":
        st.sidebar.success(f"✅ RIMBORSO: {risultato:,.2f} €")
    else:
        st.sidebar.error(f"⚠️ DEBITO: {risultato:,.2f} €")

def show_riepilogo_forfettario(dati, tipo_b=False):
    st.sidebar.markdown("## 📊 Riepilogo Forfettario")
    st.sidebar.divider()
    st.sidebar.markdown(f"Codice ATECO: **{dati.get('codice_ateco', '—')}**")
    st.sidebar.markdown(f"Coefficiente: {dati.get('coefficiente', 0)*100:.0f}%  ·  Aliquota: {dati.get('aliquota', 0)*100:.0f}%")
    st.sidebar.divider()
    st.sidebar.markdown(f"Incassi: {dati.get('incassi', 0):,.2f} €")
    st.sidebar.markdown(f"Reddito netto: {dati.get('reddito_netto', 0):,.2f} €")
    st.sidebar.markdown(f"Imposta sostitutiva: **{dati.get('imposta_sostitutiva', 0):,.2f} €**")
    if tipo_b:
        st.sidebar.markdown(f"Contributo fisso: {dati.get('contributo_fisso', 0):,.2f} €")
        if dati.get('riduzione_35_applicata'):
            st.sidebar.success("✅ Riduzione 35% applicata")
        else:
            st.sidebar.warning("⚠️ Riduzione 35% da verificare")
    st.sidebar.divider()
    saldo = dati.get('saldo', 0)
    tipo_saldo = dati.get('saldo_tipo', 'debito')
    if tipo_saldo == "credito":
        st.sidebar.success(f"✅ CREDITO: {saldo:,.2f} €")
    else:
        st.sidebar.error(f"⚠️ SALDO A DEBITO: {saldo:,.2f} €")
    if dati.get('cash_out_totale', 0) > 0:
        st.sidebar.divider()
        st.sidebar.markdown(f"**Cash-out totale: {dati.get('cash_out_totale', 0):,.2f} €**")

def show_riepilogo_misto(dati):
    dip = dati.get("dipendente", {})
    forf = dati.get("forfettario", {})
    integ = dati.get("integrato", {})
    tipo = dati.get("tipo_forfettario", "A")

    st.sidebar.markdown("## 📊 Posizione Fiscale Integrata")
    st.sidebar.caption(f"Lato forfettario: {'Professionista' if tipo == 'A' else 'Artigiano/Commerciante'}")
    st.sidebar.divider()
    st.sidebar.markdown("### 👔 Lato Dipendente")
    st.sidebar.markdown(f"IRPEF netta: **{dip.get('irpef_netta', 0):,.2f} €**")
    r1, t1 = dip.get('risultato', 0), dip.get('risultato_tipo', 'rimborso')
    (st.sidebar.success if t1 == "rimborso" else st.sidebar.error)(f"{'✅' if t1=='rimborso' else '⚠️'} {t1.capitalize()}: {r1:,.2f} €")
    st.sidebar.divider()
    st.sidebar.markdown("### 📋 Lato Forfettario")
    st.sidebar.markdown(f"Imposta sostitutiva: **{forf.get('imposta_sostitutiva', 0):,.2f} €**")
    if tipo == "B" and forf.get('contributo_fisso', 0) > 0:
        st.sidebar.markdown(f"Contributo fisso: {forf.get('contributo_fisso', 0):,.2f} €")
    r2, t2 = forf.get('saldo', 0), forf.get('saldo_tipo', 'debito')
    (st.sidebar.success if t2 == "credito" else st.sidebar.error)(f"{'✅' if t2=='credito' else '⚠️'} Saldo {t2}: {r2:,.2f} €")
    st.sidebar.divider()
    st.sidebar.markdown("### 🔗 Quadro Unificato")
    cash = integ.get('cash_flow_netto_totale', 0)
    (st.sidebar.success if cash >= 0 else st.sidebar.error)(f"💰 Cash-flow netto: {cash:+,.2f} €")
    st.sidebar.warning(f"⚠️ Soglia più vicina: **{integ.get('soglia_piu_vicina', '—')}**")

PROFILI = {
    "dipendente": {
        "nome": "Lavoratore dipendente",
        "descrizione": "Nessuna partita IVA",
        "prompt": SYSTEM_PROMPT_DIPENDENTE,
        "icona": "🏛️",
        "messaggio_iniziale": "Ciao, ho bisogno di aiuto con la mia dichiarazione dei redditi.",
        "show_func": show_riepilogo_dipendente
    },
    "forfettario_a": {
        "nome": "Partita IVA forfettaria — Professionista",
        "descrizione": "Consulente, libero professionista",
        "prompt": SYSTEM_PROMPT_FORFETTARIO_A,
        "icona": "📋",
        "messaggio_iniziale": "Ciao, ho bisogno di aiuto con la mia dichiarazione come professionista forfettario.",
        "show_func": lambda d: show_riepilogo_forfettario(d, tipo_b=False)
    },
    "forfettario_b": {
        "nome": "Partita IVA forfettaria — Artigiano/Commerciante",
        "descrizione": "Idraulico, parrucchiere, negozio, ecc.",
        "prompt": SYSTEM_PROMPT_FORFETTARIO_B,
        "icona": "🛠️",
        "messaggio_iniziale": "Ciao, ho bisogno di aiuto con la mia dichiarazione come artigiano/commerciante forfettario.",
        "show_func": lambda d: show_riepilogo_forfettario(d, tipo_b=True)
    },
    "misto": {
        "nome": "Dipendente + Partita IVA forfettaria",
        "descrizione": "Entrambe le situazioni insieme",
        "prompt": SYSTEM_PROMPT_MISTO,
        "icona": "🔗",
        "messaggio_iniziale": "Ciao, sono lavoratore dipendente e ho anche una partita IVA forfettaria. Ho bisogno di aiuto.",
        "show_func": show_riepilogo_misto
    }
}

# ============================================================
# INTERFACCIA
# ============================================================

st.set_page_config(page_title="Agente Fiscale Italiano", page_icon="🇮🇹", layout="wide")

# PROTEZIONE ACCESSO - password semplice per limitare l'uso ai soli tester invitati
if "autenticato" not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.title("🇮🇹 Agente Fiscale Italiano")
    st.caption("Accesso riservato — versione di test")
    pwd = st.text_input("Password di accesso", type="password")
    if st.button("Entra"):
        password_corretta = st.secrets.get("APP_PASSWORD", "")
        if pwd == password_corretta and password_corretta != "":
            st.session_state.autenticato = True
            st.rerun()
        else:
            st.error("Password non corretta.")
    st.stop()

if "profilo" not in st.session_state:
    st.session_state.profilo = None

if st.session_state.profilo is None:
    st.title("🇮🇹 Agente Fiscale Italiano")
    st.caption("Seleziona il profilo che corrisponde alla tua situazione")
    st.divider()

    cols = st.columns(2)
    chiavi = list(PROFILI.keys())
    for i, chiave in enumerate(chiavi):
        p = PROFILI[chiave]
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"### {p['icona']} {p['nome']}")
                st.caption(p['descrizione'])
                if st.button("Seleziona", key=f"btn_{chiave}", use_container_width=True):
                    st.session_state.profilo = chiave
                    st.rerun()

else:
    profilo = PROFILI[st.session_state.profilo]

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.started = False
        st.session_state.riepilogo = None

    LIMITE_MESSAGGI = 40
    num_messaggi_utente = sum(1 for m in st.session_state.messages if m["role"] == "user")

    st.title(f"{profilo['icona']} {profilo['nome']}")
    if st.button("← Cambia profilo"):
        for key in ["profilo", "messages", "started", "riepilogo"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.divider()

    if not st.session_state.started:
        with st.spinner("Avvio in corso..."):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=profilo["prompt"],
                tools=WEB_SEARCH_TOOL,
                messages=[{"role": "user", "content": profilo["messaggio_iniziale"]}]
            )
            opening = "".join(b.text for b in response.content if hasattr(b, "text"))
            st.session_state.messages.append({"role": "user", "content": profilo["messaggio_iniziale"]})
            st.session_state.messages.append({"role": "assistant", "content": opening})
            st.session_state.started = True

    if st.session_state.riepilogo:
        profilo["show_func"](st.session_state.riepilogo)

    for message in st.session_state.messages:
        if message["role"] == "user" and message == st.session_state.messages[0]:
            continue
        with st.chat_message(message["role"]):
            st.markdown(clean_text(message["content"]))

    if num_messaggi_utente >= LIMITE_MESSAGGI:
        st.warning("⚠️ Hai raggiunto il limite di messaggi per questa sessione di test. Per continuare, clicca su **Cambia profilo** qui sopra e avvia una nuova conversazione.")
    elif prompt := st.chat_input("Scrivi qui..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(""):
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    system=profilo["prompt"],
                    tools=WEB_SEARCH_TOOL,
                    messages=st.session_state.messages
                )
                reply = "".join(b.text for b in response.content if hasattr(b, "text"))
                dati = extract_json(reply)
                if dati:
                    st.session_state.riepilogo = dati
                st.markdown(clean_text(reply))

        st.session_state.messages.append({"role": "assistant", "content": reply})

        if st.session_state.riepilogo:
            profilo["show_func"](st.session_state.riepilogo)
            st.rerun()
