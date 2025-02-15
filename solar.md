# Solar charging algorithm



| Powers | Descrition                                                   |
| ------ | ------------------------------------------------------------ |
| Phome  | Is the power absorbed by the Home. Is always positive.       |
| Ppv    | Is the power produced by the photovoltaic system is alwais negative |
| Pevse  | Is teh power absorbed by the car us alwais positive          |
| Pgrid  | Is tbe power absorbed or produced by the home. Can be positive is the is home loads (with evse) is greater than the photovoltaic production. Is negative in the  photovoltaic production is greater than the home loads (with evse). |
| Mgrid  | Is a fixed parameter that tell the EVSE to interrupt charging if Pgid is greater than Mgrid. If you are consuming more that Mgrid. |

The following image show the schematic of the system take in account.

![Schema](images/prismsolar.png)

To compute how much power the Evse will provide to the car we can use the following formula **Pevse = Ppv + Mgrid - Phome** with the condition that Pevse is greater than 1320W in a single phase system or 3900W in a triphase system. otherwise the Evse will disconnect the charge. Because a Type2 connector  can't charge below than **6A** which is **1.3Kw** using a single phase and **3.9Kwh** using three phase.



| Phome | Ppv   | Pevse      | Pgrid |
| ----- | ----- | ---------- | ----- |
| 200W  | 800W  | 1320W (6A) | 800W  |
| 200W  | 1050W | 1320W (6A) | 470W  |
| 200W  | 1320W |            |       |

