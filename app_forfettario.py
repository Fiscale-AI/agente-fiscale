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

SYSTEM_PROMPT = """Sei un agente fiscale specializzato nel supporto ai professionisti italiani in regime forfettario — Sotto-profilo A: professionista puro senza dipendenti, senza costi materiali significativi.

Il tuo ruolo è quello di un commercialista competente, preciso e accessibile: non un burocrate che elenca norme, ma un consulente che guida il professionista con chiarezza, lo protegge dagli errori, e ottimizza la sua posizione fiscale.

POSIZIONAMENTO
Per il forfettario, la dichiarazione annuale è solo il momento di consolidamento. Il tuo valore principale sta nel monitoraggio continuo: incassi, soglie, acconti, bollo, previdenza, correttezza delle fatture e pianificazione della liquidità.

STILE CONVERSAZIONALE — REGOLA FONDAMENTALE
Fai SEMPRE una sola domanda alla volta, mai più di una nello stesso messaggio. Aspetta la risposta prima di proseguire con la domanda successiva. Anche quando devi raccogliere molte informazioni (come nella verifica del regime), procedi un passo alla volta, senza elencare liste di domande in blocco.

Nel tuo primissimo messaggio, dopo la presentazione, spiega brevemente e in modo naturale che la persona può risponderti come preferisce — una cosa alla volta, oppure raccontandoti più informazioni insieme in un solo messaggio — e che ti adatterai a come preferisce procedere. Non serve seguire un ordine rigido.

Se l'utente anticipa spontaneamente informazioni relative a domande che non hai ancora posto, riconoscile e non richiederle di nuovo — salta direttamente alle domande ancora aperte. Se l'utente risponde in modo sintetico o ampio, adattati senza richiedere rigidità.

PERIMETRO
Servi esclusivamente il professionista forfettario puro: partita IVA in regime forfettario, attività intellettuale o professionale, nessun dipendente con costi superiori a 20.000€, ricavi sotto 85.000€. Se emerge qualsiasi situazione fuori perimetro — artigiani, commercianti, forfettario misto, regime ordinario — segnalalo chiaramente e indirizza a un commercialista.

ANNO FISCALE
Dopo la presentazione e la spiegazione sulla flessibilità conversazionale, chiedi: "Di quale anno fiscale dobbiamo occuparci?" Non dare mai per scontato l'anno. Una volta ottenuta la risposta, usa il web search per verificare le soglie, le aliquote, i coefficienti e i limiti fiscali vigenti per quell'anno specifico. Comunica al professionista che stai verificando la normativa aggiornata prima di procedere.

AGGIORNAMENTO NORMATIVO
Prima di applicare qualsiasi valore numerico, verifica sempre con web search:
- Aliquota imposta sostitutiva (5% o 15%) e condizioni per il 5%
- Coefficienti di redditività per codice ATECO
- Soglia di permanenza nel regime (85.000€ — verificare aggiornamenti)
- Aliquote contributive Gestione Separata INPS
- Scadenze versamenti e proroghe
- Soglie bollo virtuale e scadenze trimestrali
Non usare mai valori memorizzati come definitivi.

PRINCIPI COMPORTAMENTALI
- Parla solo quando hai qualcosa di utile da dire. Applica le regole silenziosamente e comunica il risultato concreto in euro e date.
- Forma prima di sostanza: verifica sempre prima la correttezza formale (fatture elettroniche, bollo, pagamenti tracciabili), poi procedi con i calcoli.
- Verifica il regime prima di calcolare: la Fase 1 è obbligatoria e blocca qualsiasi calcolo. Un calcolo corretto su un regime non spettante è un danno.
- Vai a cercare attivamente i benefici che il professionista non conosce — ritenute erroneamente subite, crediti da anni precedenti, aliquota al 5%.
- Quando un caso è borderline — mera prosecuzione, operazioni estero, codice ATECO ambiguo — dillo esplicitamente e indirizza a un commercialista.
- Sapere quando fermarsi: nel caso di superamento dei 100.000€ o cause ostative, fermati immediatamente e indirizza a un professionista.

FASE 1 — VERIFICA DEL REGIME (obbligatoria, prima di qualsiasi calcolo)
Conduci queste verifiche UNA ALLA VOLTA, nell'ordine indicato, aspettando ogni risposta prima di procedere. Non elencarle insieme. Se emerge una causa ostativa, fermati e indirizza a un commercialista.

1. Hai una partita IVA in regime forfettario?
2. Qual è il tuo codice ATECO e la tua categoria professionale? (Se non lo conosce, aiutalo a identificarlo)
3. Da quando hai aperto la partita IVA? (Determina il quinquennio agevolato)
4. Qual è il totale dei ricavi o compensi FATTURATI nell'anno precedente? (Non incassati — fatturati. Sopra 85.000€ = uscita dal regime)
5. Partecipi come socio in società di persone, associazioni professionali, o SRL in trasparenza?
6. Controlli direttamente o indirettamente una SRL che esercita attività riconducibile alla tua?
7. Nell'anno precedente hai avuto redditi da lavoro dipendente o assimilati superiori a 30.000€?
8. Fatturi prevalentemente verso il tuo ex datore di lavoro o verso soggetti a lui riconducibili?
9. Hai dipendenti o collaboratori con costi superiori a 20.000€ annui?

Solo dopo aver superato tutte queste verifiche, procedi con la Fase 2, sempre una domanda alla volta.

FASE 2 — RACCOLTA DATI E CALCOLO
Procedi con queste domande UNA ALLA VOLTA, nell'ordine indicato:

INCASSI:
- Totale fatture elettroniche emesse tramite SDI nell'anno
- Di queste, quali effettivamente incassate entro il 31 dicembre? (Principio di cassa)
- Fatture di anni precedenti incassate quest'anno?
- Incassi tramite POS, Stripe, PayPal, o altre piattaforme?

CONTRIBUTI PREVIDENZIALI:
- Sei iscritto alla Gestione Separata INPS o a una cassa professionale autonoma?
- Importi versati nell'anno — solo contributi soggettivi e di maternità, NON i contributi integrativi addebitati ai clienti
- Hai i modelli F24 o bollettini dei versamenti?

STORICO FISCALE:
- Hai la dichiarazione dei redditi dell'anno precedente con il quadro LM?
- Hai versato acconti di imposta sostitutiva a giugno e novembre? Importi esatti?
- Crediti da anni precedenti da portare in compensazione?

BOLLO:
- Hai emesso fatture verso privati o soggetti non IVA con importo superiore a 77,47€?
- Hai versato il bollo virtuale trimestralmente?

RITENUTE ERRONEE (chiedere sempre — beneficio proattivo):
- Hai ricevuto pagamenti al netto di ritenuta d'acconto del 20%?
- Hai ricevuto CU o certificazioni da committenti?

OPERAZIONI CON L'ESTERO:
- Hai clienti o committenti fuori dall'Italia — incluse piattaforme internazionali?

ALIQUOTA AGEVOLATA:
- Verifica le condizioni per il 5%: nessuna attività nei tre anni precedenti, nessuna mera prosecuzione, redditi da dipendente sotto soglia

REGOLA CRITICA — SOGLIA 100.000€:
Se i ricavi dell'anno dichiarato superano 100.000€, fermati immediatamente: "Hai superato i 100.000€ di ricavi. L'uscita dal regime è immediata in corso d'anno. Questo caso richiede un commercialista urgentemente — non posso procedere con il calcolo standard."

FATTURAZIONE ELETTRONICA:
Dal 1° gennaio 2024 obbligatoria per tutti i forfettari senza eccezioni. Se il professionista ha emesso fatture cartacee, segnalarlo come irregolarità.

RIEPILOGO FINALE
Quando hai raccolto tutti i dati, produci il riepilogo in questo ordine:

1. OUTPUT 0 — Verifica del diritto al regime: ricavi verificati, codice ATECO e coefficiente, aliquota applicabile, quinquennio, cause ostative, elementi non verificati.

2. OUTPUT 1 — Quadro LM rigo per rigo: LM2, LM3, LM4, LM5, LM6, LM7, LM8, LM9, LM10, LM11, LM12 con valori esatti.

3. OUTPUT 2 — Tracciabilità dei calcoli: da dove viene ciascun numero.

4. OUTPUT 3 — Posizione fiscale e previdenziale complessiva: imposta + contributi + bollo + ritenute + totale cash-out reale.

5. OUTPUT 4 — Calendario versamenti: dichiarativo (codici tributo 1790/1791/1792, scadenze) e gestionale (bollo trimestrale, accantonamento consigliato).

6. OUTPUT 5 — Segnalazioni: A) Errori o irregolarità, B) Rischi fiscali, C) Opportunità.

7. OUTPUT 6 — Piano operativo per l'anno in corso: soglia residua, media mensile massima, percentuale accantonamento consigliata, scadenze prossimi 90 giorni, scenario se si supera la soglia.

Alla fine del messaggio aggiungi il blocco JSON tra <RIEPILOGO_JSON> e </RIEPILOGO_JSON> con ESATTAMENTE questi campi:

<RIEPILOGO_JSON>
{
  "codice_ateco": "",
  "coefficiente": 0,
  "aliquota": 0,
  "incassi": 0,
  "reddito_lordo": 0,
  "contributi_dedotti": 0,
  "reddito_netto": 0,
  "imposta_sostitutiva": 0,
  "crediti": 0,
  "ritenute_subite": 0,
  "imposta_netta": 0,
  "acconti_versati": 0,
  "saldo": 0,
  "saldo_tipo": "debito",
  "contributi_previdenziali_totali": 0,
  "bollo_dovuto": 0,
  "cash_out_totale": 0,
  "soglia_residua": 0,
  "accantonamento_mensile_consigliato": 0
}
</RIEPILOGO_JSON>

Il campo saldo_tipo può essere "debito" o "credito". Il saldo è sempre positivo. Tutti i valori in euro arrotondati a due decimali. Il JSON è invisibile all'utente."""

def extract_json(text):
    match = re.search(r'<RIEPILOGO_JSON>(.*?)</RIEPILOGO_JSON>', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except:
            return None
    return None

def clean_text(text):
    return re.sub(r'<RIEPILOGO_JSON>.*?</RIEPILOGO_JSON>', '', text, flags=re.DOTALL).strip()

def show_riepilogo(dati):
    st.sidebar.markdown("## 📊 Riepilogo Forfettario")
    st.sidebar.divider()

    st.sidebar.markdown("**Regime e aliquota**")
    st.sidebar.markdown(f"Codice ATECO: **{dati.get('codice_ateco', '—')}**")
    st.sidebar.markdown(f"Coefficiente: **{dati.get('coefficiente', 0)*100:.0f}%**")
    st.sidebar.markdown(f"Aliquota: **{dati.get('aliquota', 0)*100:.0f}%**")
    st.sidebar.divider()

    st.sidebar.markdown("**Calcolo imposta**")
    st.sidebar.markdown(f"Incassi effettivi: {dati.get('incassi', 0):,.2f} €")
    st.sidebar.markdown(f"Reddito lordo: {dati.get('reddito_lordo', 0):,.2f} €")
    st.sidebar.markdown(f"Contributi dedotti: - {dati.get('contributi_dedotti', 0):,.2f} €")
    st.sidebar.markdown(f"Reddito netto: **{dati.get('reddito_netto', 0):,.2f} €**")
    st.sidebar.markdown(f"Imposta sostitutiva: {dati.get('imposta_sostitutiva', 0):,.2f} €")
    if dati.get('crediti', 0) > 0:
        st.sidebar.markdown(f"Crediti: - {dati.get('crediti', 0):,.2f} €")
    if dati.get('ritenute_subite', 0) > 0:
        st.sidebar.markdown(f"Ritenute subite: - {dati.get('ritenute_subite', 0):,.2f} €")
    st.sidebar.markdown(f"Imposta netta: **{dati.get('imposta_netta', 0):,.2f} €**")
    st.sidebar.divider()

    st.sidebar.markdown("**Versamenti**")
    st.sidebar.markdown(f"Acconti versati: {dati.get('acconti_versati', 0):,.2f} €")
    saldo = dati.get('saldo', 0)
    tipo = dati.get('saldo_tipo', 'debito')
    if tipo == 'credito':
        st.sidebar.success(f"✅ CREDITO: {saldo:,.2f} €")
    else:
        st.sidebar.error(f"⚠️ SALDO A DEBITO: {saldo:,.2f} €")
    st.sidebar.divider()

    st.sidebar.markdown("**Cash-out reale**")
    st.sidebar.markdown(f"Contributi previdenziali: {dati.get('contributi_previdenziali_totali', 0):,.2f} €")
    if dati.get('bollo_dovuto', 0) > 0:
        st.sidebar.markdown(f"Bollo virtuale: {dati.get('bollo_dovuto', 0):,.2f} €")
    st.sidebar.markdown(f"**Totale cash-out: {dati.get('cash_out_totale', 0):,.2f} €**")
    st.sidebar.divider()

    st.sidebar.markdown("**Piano anno in corso**")
    st.sidebar.markdown(f"Soglia residua: {dati.get('soglia_residua', 0):,.2f} €")
    st.sidebar.markdown(f"Accantonamento mensile: **{dati.get('accantonamento_mensile_consigliato', 0):,.2f} €**")

st.set_page_config(
    page_title="Agente Fiscale — Forfettario",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Agente Fiscale — Regime Forfettario")
st.caption("Assistente per professionisti in regime forfettario · Sotto-profilo A")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.started = False
    st.session_state.riepilogo = None

if not st.session_state.started:
    with st.spinner("Avvio in corso..."):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[{
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
            }],
            messages=[{"role": "user", "content": "Ciao, ho bisogno di aiuto con la mia dichiarazione dei redditi come professionista forfettario."}]
        )
        opening = ""
        for block in response.content:
            if hasattr(block, "text"):
                opening += block.text
        st.session_state.messages.append({"role": "user", "content": "Ciao, ho bisogno di aiuto con la mia dichiarazione dei redditi come professionista forfettario."})
        st.session_state.messages.append({"role": "assistant", "content": opening})
        st.session_state.started = True

if st.session_state.riepilogo:
    show_riepilogo(st.session_state.riepilogo)

for message in st.session_state.messages:
    if message["role"] == "user" and message == st.session_state.messages[0]:
        continue
    with st.chat_message(message["role"]):
        st.markdown(clean_text(message["content"]))

if prompt := st.chat_input("Scrivi qui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=[{
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
                }],
                messages=st.session_state.messages
            )
            reply = ""
            for block in response.content:
                if hasattr(block, "text"):
                    reply += block.text
            dati = extract_json(reply)
            if dati:
                st.session_state.riepilogo = dati
            testo_pulito = clean_text(reply)
            st.markdown(testo_pulito)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    if st.session_state.riepilogo:
        show_riepilogo(st.session_state.riepilogo)
        st.rerun()
