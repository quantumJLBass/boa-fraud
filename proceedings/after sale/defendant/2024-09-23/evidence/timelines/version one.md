---
noteID: 73785b0b-cbe0-498c-9d3f-1d5e44778441
---
```mermaid
flowchart TD
    %% Define styles for clarity
    classDef entityStyle fill:#f0f0f0,stroke:#333,stroke-width:1px,font-size:12px;
    classDef loanStyle fill:#d0f0fd,stroke:#0077b6,stroke-width:2px;
    classDef breakStyle fill:#fde2e4,stroke:#d00000,stroke-width:2px;
    classDef legalStyle fill:#fff4e6,stroke:#f48c06,stroke-width:2px;
    classDef remakeStyle fill:#d8f3dc,stroke:#40916c,stroke-width:2px;
    classDef actionStyle fill:#eae2b7,stroke:#dda15e,stroke-width:2px;
    classDef courtStyle fill:#e9ecef,stroke:#495057,stroke-width:2px;
    classDef highlightStyle stroke:#ff006e,stroke-width:3px;

    %% Entities
    subgraph Entities
        direction TB
        ZFNB[Zions First National Bank N.A.]:::entityStyle
        CW[Countrywide]:::entityStyle
        BAC[BAC Home Loans Servicing, LP]:::entityStyle
        BoA[Bank of America, N.A.]:::entityStyle
        CMS[Carrington Mortgage Services LLC]:::entityStyle
        MERS[MERS]:::entityStyle
        JLB[Jeremy L. Bass]:::entityStyle
        AMB[Aimee M. Bass]:::entityStyle
        SoHUD[Secretary of Housing and Urban Development]:::entityStyle
        IDEA[IDEA Law Group LLC]:::entityStyle
        DPW[DPW Enterprises LLC]:::entityStyle
        MP[Mountain Prime 2018 LLC]:::entityStyle
        Court[Court]:::courtStyle
    end

    %% Loan Origination (2008-09-04)
    JLB -->|Deed of Trust<br>(760926, $148,418.00)| ZFNB:::loanStyle
    ZFNB -->|Funds Loan<br>($148,418.00)| JLB:::loanStyle

    %% Transfer to Countrywide (2008-10-01)
    ZFNB -.->|Transfers Loan| CW:::loanStyle
    CW -->|Notice of Transfer| JLB

    %% Transfer to BAC (2009-10-01)
    CW -.->|Transfers Loan| BAC:::loanStyle
    BAC -->|Transfer Notice| JLB

    %% Promissory Note to BoA (2009-10-16)
    JLB -->|Promissory Note<br>($148,614.00)| BoA:::loanStyle
    JLB -->|Deed of Trust<br>(774964)| BoA:::loanStyle

    %% Break in Loan Lineage (2009-11-02)
    BoA -->|Substitution of Trustee<br>(775251)| BreakPoint[Break in Loan Lineage]:::breakStyle
    BoA -->|Letter of Full Reconveyance<br>(775252)| JLB:::breakStyle

    %% Assignment to MERS (2012-03-20)
    BAC -.->|Assignment of Deed of Trust<br>(799540)| MERS:::remakeStyle
    MERS -.->|Holds Interest| BAC

    %% Loan Modification with CMS (2012-09-14)
    JLB -->|Loan Modification<br>Agreement ($142,709.46)| CMS:::remakeStyle
    JLB -->|Subordinate Note<br>($7,392.91)| SoHUD:::remakeStyle

    %% Forbearance Period (2020-07-31 to 2022-06-18)
    JLB -->|Requests Forbearance| CMS
    CMS -->|Forbearance Granted<br>(23 Months)| JLB:::actionStyle

    %% Default and Foreclosure Initiation (2022-06-18)
    CMS -->|Notice of Intent to Foreclose<br>($24,650.38)| JLB:::legalStyle
    CMS -->|Appoints Successor Trustee<br>(902078)| IDEA:::legalStyle

    %% Foreclosure Proceedings
    IDEA -->|Notice of Default<br>(902262, $139,529.94)| JLB:::legalStyle
    JLB -->|Cease and Desist Letter<br>(2022-12-12)| IDEA:::legalStyle
    JLB -->|Files Complaint<br>(CV35-22-1875)| Court:::legalStyle
    Court -->|Denies TRO<br>(2023-02-17)| JLB
    IDEA -->|Schedules Trustee's Sale<br>(2022-12-30)| JLB:::legalStyle
    IDEA -->|Postpones Trustee's Sale| JLB:::legalStyle
    IDEA -->|Trustee Sale Conducted<br>(2024-02-29)| DPW:::loanStyle
    IDEA -->|Issues Trustee's Deed<br>(912874)| DPW:::loanStyle
    DPW -->|Transfers Property| MP

    %% Eviction Process
    MP -->|Notice to Vacate<br>(2024-03-21)| JLB:::legalStyle

    %% Post-Foreclosure Legal Actions
    JLB -->|Files Post-Foreclosure Complaint<br>(CV35-24-1063)| Court:::legalStyle
    Court -->|Grants Partial Summary Judgment<br>(2024-11-05)| JLB
    JLB -->|Files Motion for Reconsideration<br>(2024-11-06)| Court

    %% Connections and Flow
    class BreakPoint breakStyle
    style BreakPoint stroke-dasharray: 5 5

    %% Highlights
    class JLB,BoA highlightStyle

    %% Legends
    subgraph Legends [ ]
        direction LR
        LoanFlow[Loan Transactions]:::loanStyle
        BreakLineage[Break in Lineage]:::breakStyle
        RemakeLoan[Remake of Loan]:::remakeStyle
        LegalActions[Legal Actions]:::legalStyle
        Actions[Processes/Actions]:::actionStyle
        CourtEntity[Court]:::courtStyle
    end

```

```mermaid
gantt
    %%{
    init: {
        "gantt": {
            'topPadding' : 125,
            'rightPadding' : 10,
            'leftPadding' : 250,
            'barHeight' : 10,
            'fontSize' : 10,
            'titleTopMargin': 75,
            'gridLineStartPadding' : 2,
            'barGap' : 5,
            'sectionFontSize': 10,
		    'numberSectionStyles': 3,
		    'axisFormat': '%Y/%m',
		    'topAxis': true
        },
        'theme': 'base',
        'themeVariables': {
	        "background":'#f4f4f4',
	        "titleColor":"#000000",
            "fontFamily": 'Sans-Serif',
            'primaryColor': '#c02d2d',
            'primaryTextColor': '#fff',
            'primaryBorderColor': '#82092d'
        }
    }
    }%%
    title Complete Timeline of Events
    dateFormat  YYYY-MM-DD
    axisFormat  %Y
    tickInterval 1year

    section Loan Origination and Initial Deeds
    Deed of Trust (760926, $148,418.00)          :milestone, 2008-09-04, 0d
    Warranty Deed (760924, $10.00)               :milestone, 2008-09-05, 0d
    Quitclaim Deed (760925)                      :milestone, 2008-09-05, 0d

    section Loan Transfers and Assignments
    Notice of Transfer ($146,418.00)             :milestone, 2008-10-01, 0d
    Transfer Notice (CW to BAC)                  :milestone, 2009-10-01, 0d
    Promissory Note to BoA ($148,614.00)         :milestone, 2009-10-16, 0d
    Deed of Trust (774964, $148,614.00)          :milestone, 2009-10-16, 0d
    Transfer Notice (BoA to BAC)                 :milestone, 2009-10-30, 0d

    section Loan Reconveyance
    Substitution of Trustee (775251)             :milestone, 2009-11-02, 0d
    Letter of Full Reconveyance (775252)         :milestone, 2009-11-02, 0d

    section Further Loan Modifications
    Assignment of Deed of Trust (799540)         :milestone, 2012-03-20, 0d
    Loan Modification Agreement ($142,709.46)    :milestone, 2012-09-14, 0d
    Subordinate Note ($7,392.91)                 :milestone, 2012-09-14, 0d
    Subordinate Note to SoHUD ($7,392.91)        :milestone, 2012-09-14, 0d
    Notice of Servicing Transfer to Carrington   :milestone, 2017-10-07, 0d

    section Forbearance Period
    Forbearance Initiated                        :milestone, 2020-07-31, 0d
    Forbearance Period 23 Months                           :2020-07-31, 2022-06-18
    Forbearance Legal End                        :milestone, 2022-01-01, 0d
    Loan Modification Offered ($14,390.38)       :milestone, 2022-03-15, 0d
    Forbearance Extended to 23 Months            :milestone, 2022-04-26, 0d
    Forbearance End Letter                       :milestone, 2022-06-18, 0d

    section Default and Foreclosure Initiation
    Notice of Intent to Foreclose ($24,650.38)   :milestone, 2022-06-18, 0d
    Appointment of Successor Trustee (902078)    :milestone, 2022-08-02, 0d
    Notice of Default (902262, $139,529.94)      :milestone, 2022-08-17, 0d

    section Foreclosure Proceedings
    Affidavits and Notices                       :2022-08-17, 2024-01-29
    Affidavit of Mailing (904186)                :milestone, 2022-08-17, 0d
    Affidavit of Compliance (904187)             :milestone, 2022-08-19, 0d
    Affidavit of Compliance Recorded (904188)    :milestone, 2022-08-23, 0d
    Affidavit of Publication (904190)            :milestone, 2022-08-24, 0d
    Affidavit of Service (904189)                :milestone, 2022-08-31, 0d
    Cease and Desist Letter Sent                 :milestone, 2022-12-12, 0d
    Complaint and Summons Filed (CV35-22-1875)   :milestone, 2022-12-27, 0d
    Trustee's Sale Scheduled                     :milestone, 2022-12-30, 0d
    Motion to Dismiss Filed                      :milestone, 2023-01-17, 0d
    Hearing on Motion to Dismiss                 :milestone, 2023-01-26, 0d
    Court Denies TRO                             :milestone, 2023-02-17, 0d
    Appointment of Successor Trustee (906092)    :milestone, 2023-02-23, 0d
    Court Denies Reconsideration                 :milestone, 2023-03-09, 0d
    Affidavit Confirming Postponed Sale (912340) :milestone, 2024-01-29, 0d
    Trustee Sale Conducted                       :milestone, 2024-02-29, 0d
    Trustee's Deed Issued (912874, $165,346.71)  :milestone, 2024-03-01, 0d

    section Eviction Process
    Notice to Vacate Sent                        :milestone, 2024-03-21, 0d
    Notice to Vacate Received                    :milestone, 2024-03-25, 0d
    Follow-up Email to Authorities               :milestone, 2024-05-02, 0d

    section Legal Actions and Court Proceedings
    Post-Foreclosure Complaint Filed (CV35-24-1063) :milestone, 2024-07-08, 0d
    Motion for Co-Counsel Appointment            :milestone, 2024-08-13, 0d
    Plaintiffs' Summary Judgment Motion          :milestone, 2024-09-16, 0d
    Status Conferences                           :2024-09-17, 2024-10-08
    Status Conference Held                       :milestone, 2024-09-17, 0d
    Status Conference Held                       :milestone, 2024-10-08, 0d
    Response to Summary Judgment Filed           :milestone, 2024-10-15, 0d
    Plaintiffs' Reply Memorandum Filed           :milestone, 2024-10-18, 0d
    Defendant's Reply Memorandum Filed           :milestone, 2024-10-21, 0d
    Hearing on Summary Judgment                  :milestone, 2024-10-22, 0d
    Court Grants Summary Judgment in Part        :milestone, 2024-11-05, 0d
    Motion for Reconsideration Filed             :milestone, 2024-11-06, 0d
    Hearing for Reconsideration Scheduled        :milestone, 2024-12-10, 0d
	
	todayMarker stroke-width:5px,stroke:#0f0,opacity:0.5  


```


```mermaid
flowchart LR
    %% Define styles for clarity
    classDef entityStyle fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef loanStyle fill:#e0f7fa,stroke:#0288d1,stroke-width:2px;
    classDef breakStyle fill:#ffebee,stroke:#d32f2f,stroke-width:2px;
    classDef legalStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef remakeStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef actionStyle fill:#f1f8e9,stroke:#8bc34a,stroke-width:2px;

    %% Entities
    subgraph Entities
        direction TB
        ZFNB[Zions First National Bank N.A.]:::entityStyle
        CW[Countrywide]:::entityStyle
        BAC[BAC Home Loans Servicing, LP]:::entityStyle
        BoA[Bank of America, N.A.]:::entityStyle
        CMS[Carrington Mortgage Services LLC]:::entityStyle
        MERS[MERS]:::entityStyle
        JLB[Jeremy L. Bass]:::entityStyle
        SoHUD[Secretary of Housing and Urban Development]:::entityStyle
        IDEA[IDEA Law Group LLC]:::entityStyle
        DPW[DPW Enterprises LLC]:::entityStyle
        MP[Mountain Prime 2018 LLC]:::entityStyle
    end

    %% Loan Origination
    ZFNB -- Loan Origination --> JLB:::loanStyle
    JLB -- Deed of Trust (760926) --> ZFNB:::loanStyle

    %% Loan Transfer to CW
    ZFNB -- Transfers Loan --> CW:::loanStyle
    CW -- Notice of Transfer --> JLB

    %% Loan Transfer to BAC
    CW -- Transfers Loan --> BAC:::loanStyle
    BAC -- Transfer Notice --> JLB

    %% New Promissory Note to BoA
    JLB -- Promissory Note ($148,614.00) --> BoA:::loanStyle
    JLB -- Deed of Trust (774964) --> BoA:::loanStyle

    %% Break in Loan Lineage
    class BreakInLineage breakStyle
    BoA -- Substitution of Trustee --> BreakInLineage:::breakStyle
    BreakInLineage -- Letter of Full Reconveyance --> JLB

    %% Assignment to MERS (Possible Remake)
    MERS -- Assignment of Deed of Trust (799540) --> BAC:::remakeStyle
    BAC -- Assigns Interest --> MERS:::remakeStyle

    %% Loan Modification
    JLB -- Loan Modification Agreement --> CMS:::remakeStyle
    CMS -- Subordinate Note --> SoHUD:::remakeStyle

    %% Forbearance Period
    JLB -- Forbearance Agreement --> CMS
    class ForbearancePeriod actionStyle
    CMS -- Forbearance Period (2020-07-31 to 2022-06-18) --> ForbearancePeriod:::actionStyle

    %% Default and Foreclosure Initiation
    CMS -- Notice of Intent to Foreclose --> JLB:::legalStyle
    CMS -- Appointment of Successor Trustee --> IDEA:::legalStyle

    %% Foreclosure Proceedings
    IDEA -- Notice of Default --> JLB:::legalStyle
    IDEA -- Foreclosure Proceedings --> Court:::legalStyle

    %% Trustee Sale and Transfer
    IDEA -- Trustee Sale Conducted --> DPW:::loanStyle
    IDEA -- Trustee's Deed Issued --> DPW:::loanStyle
    DPW -- Transfers Property --> MP:::loanStyle

    %% Eviction Process
    MP -- Notice to Vacate --> JLB:::legalStyle

    %% Legal Actions and Court Proceedings
    JLB -- Post-Foreclosure Complaint Filed --> Court:::legalStyle
    Court -- Summary Judgment (Partial) --> JLB:::legalStyle
    JLB -- Motion for Reconsideration --> Court:::legalStyle

    %% Connections
    %% (Specify the chronological flow)
    %% Use dotted lines to represent legal actions
    style BreakInLineage stroke-dasharray: 5 5
    style Court fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    %% Legends
    subgraph Legends [ ]
        direction LR
        L1[Loan Flow]:::loanStyle
        L2[Break in Lineage]:::breakStyle
        L3[Remake of Loan]:::remakeStyle
        L4[Legal Actions]:::legalStyle
        L5[Actions/Processes]:::actionStyle
    end

```

```mermaid
timeline
    title Complete Timeline of Events

    section Loan Origination and Initial Deeds
    2008-09 : Deed of Trust (760926, $148,418.00)
    2008-09 : Warranty Deed (760924, $10.00)
    2008-09 : Quitclaim Deed (760925)

    section Loan Transfers and Assignments
    2008-10 : Notice of Transfer ($146,418.00)
    2009-10 : Transfer Notice (CW to BAC)
    2009-10 : Promissory Note to BoA ($148,614.00)
    2009-10 : Deed of Trust (774964, $148,614.00)
    2009-11 : Substitution of Trustee (775251)
    2009-11 : Letter of Full Reconveyance (775252)
    2009-11 : Transfer Notice (BoA to BAC)

    section Further Loan Modifications
    2012-03 : Assignment of Deed of Trust (799540)
    2012-09 : Loan Modification Agreement ($142,709.46)
    2012-09 : Subordinate Note ($7,392.91)
    2012-09 : Subordinate Note to SoHUD ($7,392.91)
    2017-10 : Notice of Servicing Transfer to Carrington
    2019-12 : New Loan Packet Sent

    section Forbearance Period
    2020-07 : Forbearance Initiated
    2020-07 - 2022-06 : Forbearance Period (23 Months)
    2022-01 : Forbearance Legal End
    2022-03 : Loan Modification Offered ($14,390.38)
    2022-04 : Forbearance Extended to 23 Months
    2022-06 : Forbearance End Letter

    section Default and Foreclosure Initiation
    2022-06 : Notice of Intent to Foreclose ($24,650.38)
    2022-08 : Appointment of Successor Trustee (902078)
    2022-08 : Notice of Default (902262, $139,529.94)

    section Foreclosure Proceedings
    2022-08 - 2024-01 : Affidavits and Notices
    2022-08 : Affidavit of Mailing (904186)
    2022-08 : Affidavit of Compliance (904187)
    2022-08 : Affidavit of Compliance Recorded (904188)
    2022-08 : Affidavit of Publication (904190)
    2022-08 : Affidavit of Service (904189)
    2022-12 : Cease and Desist Letter Sent
    2022-12 : Complaint and Summons Filed (CV35-22-1875)
    2022-12 : Trustee's Sale Scheduled
    2023-01 : Motion to Dismiss Filed
    2023-01 : Hearing on Motion to Dismiss
    2023-02 : Court Denies TRO
    2023-02 : Appointment of Successor Trustee (906092)
    2023-03 : Court Denies Reconsideration
    2024-01 : Affidavit Confirming Postponed Sale (912340)
    2024-02 : Trustee Sale Conducted ($165,346.71)
    2024-03 : Trustee's Deed Issued (912874)

    section Eviction Process
    2024-03 : Notice to Vacate Sent
    2024-03 : Notice to Vacate Received
    2024-05 : Follow-up Email to Authorities

    section Legal Actions and Court Proceedings
    2024-07 : Post-Foreclosure Complaint Filed (CV35-24-1063)
    2024-08 : Motion for Co-Counsel Appointment
    2024-09 : Plaintiffs' Summary Judgment Motion
    2024-09 : Status Conference Held
    2024-10 : Status Conference Held
    2024-10 : Response to Summary Judgment Filed
    2024-10 : Plaintiffs' Reply Memorandum Filed
    2024-10 : Defendant's Reply Memorandum Filed
    2024-10 : Hearing on Summary Judgment
    2024-11 : Court Grants Summary Judgment in Part
    2024-11 : Motion for Reconsideration Filed
    2024-12 : Hearing for Reconsideration Scheduled

```
