# **PRISM MQTT** 

[Prism-MQTT-4.0.pdf][https://silla.industries/wp-content/uploads/2025/11/Prism-MQTT-4.0.pdf]

## **Manuale per integrazione MQTT** 



<!-- Start of picture text -->
@<<br><!-- End of picture text -->

rel. 4.0 - rev. 20251001 

###### **Note** 

Le informazioni riportate in questo manuale potranno subire variazioni nel corso del tempo. Per avere sempre la versione aggiornata della documentazione scansionare il QR Code oppure andare all’indirizzo silla.industries/centro-assistenza 

Consulta la documentazione completa in PDF 



###### **Copyright** 

Il copyright di queste istruzioni per l'uso è di proprietà del produttore. I testi e le immagini sono riportati al livello tecnico del prodotto al momento della stampa. Silla si riserva il diritto di modificare le informazioni fornite nella documentazione. Il contenuto della documentazione non deve dar luogo a reclami da parte dell'acquirente. Silla Prism è un marchio registrato di proprietà di Silla SRL. 

### INDICE 

|**INDICE**||**1**|
|---|---|---|
|**CONFIGURAZIONE MQTT UTENTE**||**3**|
|Il protocollo MQTT<br>i||3|
|Configurazione tramite APP||3|
|**TOPIC MQTT**||**4**|
|<base_topic>||4|
|<numero_porta>||4|
|Topic di stato||5|
|hello||5|
|<numero_porta>/mode||5|
|<numero_porta>/state||5|
|<numero_porta>/volt||5|
|<numero_porta>/w||6|
|<numero_porta>/amp||6|
|<numero_porta>/pilot||6|
|<numero_porta>/user_amp||6|
|<numero_porta>/session_time||6|
|<numero_porta>/wh||6|
|<numero_porta>/wh_total||6|
|<numero_porta>/error||6|
|<numero_porta>/input/touch||7|
|energy_data/power_grid||7|
|Topic di comando||8|
|<numero_porta>/command/set_mode||8|
|<numero_porta>/command/set_current_user||8|
|<numero_porta>/command/set_current_limit||8|
|<numero_porta>/command/enable_night||8|
|<numero_porta>/command/disable_night||9|
|<numero_porta>/command/set_mode_traps '-auth'||9|
|<numero_porta>/command/set_mode_traps '+auth'||9|
|Topic di risposta ai comandi||10|
|commandresult/<comando>/success||10|
|commandresult/<comando>/error||10|
||Prism MQTT -|4.0 **- 1**|



|Topic in presenza di Powerwall|11|
|---|---|
|energy_data/power_solar|11|
|energy_data/power_house|11|



### CONFIGURAZIONE MQTT UTENTE 

#### **Il protocollo MQTT** 

**MQTT** è un protocollo standard di messaggistica progettato per situazioni in cui è richiesto un basso impatto e dove la banda è limitata. Per queste caratteristiche è un protocollo di comunicazione largamente utilizzato nell’ambito dei dispositivi IoT e della domotica. 

Prism opera come **client MQTT** , pubblicando e ricevendo messaggi attraverso il broker configurato dall’utente. 

#### **Configurazione tramite APP** 



<!-- Start of picture text -->
X Accessoe comunicaz... v<br>MOTT personalizzato @<br>Indirizzo del server (Host) 10.205.111.128<br>Porta 1883<br>Username  prism_A08545<br>Password swsesseer ©<br>Topic base  home/prism2/<br>Usa connessione<br>sicura (TLS)<br>Verifica certificato TLS -D<br><!-- End of picture text -->

Per configurare Prism nel software di domotica, utilizzare la sezione dedicata nelle impostazioni del dispositivo disponibile nell’app SILLA. 

Si faccia riferimento alla guida dedicata pubblicata nel centro assistenza. 

### TOPIC MQTT 

Nel manuale i valori tra due parentesi angolari, ad esempio “<base_topic>”, indicano variabili che vanno specificate a seconda del contesto. Di seguito sono descritti i valori variabili. 

##### <base_topic> 

corrisponde al valore specificato nelle impostazioni MQTT, come descritto nella sezione <u>Confgurazione tramite APPi .</u> 

##### <numero_porta> 

corrisponde al numero della porta di ricarica. Le Prism con un solo cavo avranno solo la porta 1 mentre per le Prism DUO la porta sarà: 

1. per il cavo di sinistra 

2. per il cavo di destra 

Nelle sezioni seguenti sono descritti i vari topic MQTT utilizzabili per Prism, divisi per categorie. 

#### **Topic di stato** 

In questi topic vengono pubblicati messaggi riguardanti lo stato di Prism. 

I messaggi vengono mandati solamente quando il valore specificato cambia, quindi in caso di valori costanti non si riceveranno ulteriori messaggi. 

##### hello 

Su questo topic viene inviato un messaggio all’avvio della comunicazione contenente informazioni sulla versione di Prism 

_Esempio: <base_topic>/hello “Prism-A00006 3.2.77 (evsemd v1.1.1)”_ 

##### <numero_porta>/mode 

Riporta la modalità attuale della porta: 

**1. Solar** 

**2. Normal** 

**3. Pausa** 

**7. Carica interrotta dal bilanciamento** (potenza disponibile insufficiente) 

_Esempio: <base_topic>/1/mode 2_ 

Indica che la porta 1 è in modalità “Normal” 

##### <numero_porta>/state 

Riporta lo stato attuale della Prism: 

**1. idle** : nessun veicolo connesso 

**2. waiting** : veicolo connesso, in attesa di ricaricare 

**3. charging** : veicolo in carica 

**4. pause** : carica in pausa 

_Esempio: <base_topic>/1/state 3_ Indica che la porta 1 è in carica. 

##### <numero_porta>/volt 

Riporta la tensione attualmente misurata da Prism, in volt [V]. 

_Esempio: <base_topic>/1/volt 220.0_ 

##### <numero_porta>/w 

Riporta la potenza attualmente erogata dalla porta di ricarica, in watt[W]. _Esempio: <base_topic>/1/w 1760.0_ 

##### <numero_porta>/amp 

Riporta la corrente attualmente erogata dalla porta di ricarica, in milliampere [mA]. 

_Esempio: <base_topic>/1/amp 8000_ 

##### <numero_porta>/pilot 

Riporta la corrente pilotata all’auto, in ampere [A]. 

_Esempio: <base_topic>/1/pilot 8_ 

##### <numero_porta>/user_amp 

Riporta la corrente impostata dall’utente, in ampere [A]. 

_Esempio: <base_topic>/1/user_amp 8_ 

##### <numero_porta>/session_time 

Riporta la durata della sessione di ricarica attuale, in secondi [s]. 

_Esempio: <base_topic>/1/session_time 3600_ 

##### <numero_porta>/wh 

Riporta l’energia erogata dalla porta di ricarica durante la sessione in corso, in wattora [Wh]. 

_Esempio: <base_topic>/1/wh 1760.0_ 

##### <numero_porta>/wh_total 

Riporta energia totale erogata da Prism, in wattora [Wh]. 

_Esempio: <base_topic>/1/wh_total 8050_ 

##### <numero_porta>/error 

Riporta il codice di errore relativo alla porta. Il valore “ **0** ” indica che non c’è nessun errore. 

##### _Esempio: <base_topic>/1/error 0_ 

##### <numero_porta>/input/touch 

In questo topic vengono riportati gli eventi relativi al pulsante touch della porta, espressi come sequenza delle durate di pressione del pulsante. Se il pulsante viene premuto più volte consecutivamente, questo evento viene riconosciuto come una **sequenza di touch** . La sequenza termina quando il pulsante non viene premuto per almeno 0.8 secondi oppure il pulsante viene premuto consecutivamente più di 30 volte. 

_Esempi_ : 

- _<base_topic>/1/input/touch “1”_ 

Il pulsante è stato premuto brevemente per una volta 

- _<base_topic>/1/input/touch “1,1,1”_ 

Il pulsante è stato premuto brevemente per tre volte 

- <base_topic>/1/input/touch “3” 

Il pulsante è stato tenuto premuto per tre secondi 

- <base_topic>/1/input/touch “1,1,3” 

Il pulsante è stato premuto brevemente per due volte, poi è stato tenuto premuto per 3 secondi 

##### energy_data/power_grid 

Riporta la potenza attualmente prelevata dalla rete, in watt [W]. Valori positivi indicano un’importazione dalla rete, mentre valori negativi indicano un’esportazione in rete. 

_Esempio: <base_topic>/energy_data/power_grid 2800_ Indica che l’impianto sta prelevando 2.8 kW dalla rete 

#### **Topic di comando** 

In questa sezione sono elencati i topic di comando. Pubblicando su questi topic infatti è possibile controllare alcuni parametri della ricarica. 

##### <numero_porta>/command/set_mode 

Imposta la modalità di Prism: 

**1. Solare** 

**2. Normale** 

**3. Pausa** 

_Esempio: <base_topic>/1/command/set_mode 2_ La porta 1 viene impostata in modalità “Normale” 

##### <numero_porta>/command/set_current_user 

Imposta la corrente massima di ricarica specificata dall’utente, in ampere [A]. Usare numeri interi senza cifre decimali. 

_Esempio: <base_topic>/1/command/set_current_user 8_ La corrente della porta 1 viene impostata a 8 ampere. 

**nota:** Questo comando è equivalente alla pressione dei pulsanti + e - dall’interfaccia web di Prism. 

**nota:** Non usare questo comando per implementare logiche di regolazione dinamica della corrente. Utilizzare invece il topic <numero_porta>/command/set_current_limit. 

##### <numero_porta>/command/set_current_limit 

Imposta il limite di corrente di ricarica, in ampere [A]. Usare numeri interi con una cifra decimale. 

Questo comando può essere utilizzato per implementare **logiche di bilanciamento personalizzate** . 

_Esempio: <base_topic>/1/command/set_current_limit 9.2_ 

##### <numero_porta>/command/enable_night 

Questo comando abilita la programmazione. 

##### <numero_porta>/command/disable_night 

Questo comando disabilita la programmazione. 

**nota:** gli orari vanno impostati preventivamente tramite app. 

##### <numero_porta>/command/set_mode_traps '-auth' 

Questo comando inoltra l’autorizzazione della ricarica. 

##### <numero_porta>/command/set_mode_traps '+auth' 

Questo comando inoltra la deautorizzazione della ricarica. 

**nota:** perché questo comando abbia effetto, il cavo di ricarica dev’essere collegato e l’autostart disabilitato. 

#### **Topic di risposta ai comandi** 

In questi topic viene pubblicato un messaggio ogni qualvolta viene eseguito un comando. 

##### commandresult/<comando>/success 

In questo topic viene mandato un messaggio quando <comando> viene eseguito correttamente. 

_Esempio:_ 

- viene mandato il comando 

_<base_topic>/1/command/set_current_limit 9.2_ 

- se viene eseguito correttamente, viene pubblicato il messaggio _<base_topic>/commandresult/set_current_limit/success_ 

##### commandresult/<comando>/error 

In questo topic viene mandato un messaggio quando <comando> non viene eseguito correttamente. 

_Esempio:_ 

- viene mandato il comando 

_<base_topic>/1/command/set_mode 54_ 

- viene pubblicato il messaggio 

_<base_topic>/commandresult/set_mode/error “Bad syntax, mode must be [0-9]”_ 

#### **Topic in presenza di Powerwall** 

I topic riportati di seguito sono disponibili solo se è abilitata la comunicazione con il **Powerwall** . Per maggiori informazioni consultare il manuale d’uso dell’app Silla, disponibile nell’area di supporto. 

##### energy_data/power_solar 

Riporta la potenza attualmente prodotta dall’impianto fotovoltaico, in watt [W]. 

_Esempio: <base_topic>/1/power_solar 3000_ 

##### energy_data/power_house 

Riporta la potenza attualmente consumata dall’impianto domestico, in watt [W]. 

_Esempio: <base_topic>/1/power_solar 3000_ 



Via dell’Artigianato, 9 35127 Padova - PD Italia 

**https://silla.industries** 

**https://silla.industries/centro-assistenza/** 

