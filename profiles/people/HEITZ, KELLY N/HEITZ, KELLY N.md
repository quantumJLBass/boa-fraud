---
page-title: Person Overview - HEITZ, KELLY
url/uri:
  - https://opencorporates.com/officers/714917946
  - https://opencorporates.com/officers/714913200
  - https://opencorporates.com/officers/776991861
  - https://opencorporates.com/officers/468911561
  - https://opencorporates.com/officers/774125031
  - https://opencorporates.com/officers/774125025
  - https://opencorporates.com/officers/774125028
  - https://opencorporates.com/officers/101014857

date: 2024-05-22
tags:
  - Company-Details/Officer-Information
  - Person-Details/General-Information
aka:
  - KELLY N HEITZ
  - [[HEITZ, KELLY N]]
  - KELLY NICHOLAS HEITZ
  - HEITZ, KELLY NICHOLAS
  - Kelly R Heitz
  - Kelly Nicolas Heitz
  - KELLY N HEITZ
  - [[HEITZ, KELLY N]]
  - KELLY NICHOLAS HEITZ
  - HEITZ, KELLY NICHOLAS
companies:
  - MOUNTAIN PRIME LLC (Illinois)
  - MPH1, LLC (Illinois)
  - MPH3, LLC (Georgia)
  - CROSS COUNTRY EQUITY, LLC (Utah)
  - [[ALL SEASONS REAL ESTATE LLC (Utah - 7053375-0160)]]
  - [[MOUNTAIN PRIME 2017 LLC BRANCH (Minnesota - cfaaa8a5-1402-e811-9155-00155d0d6f70)]]
position: manager, member
last-updated: 2022-11-11
address: [[3138 N 1250 W, PLEASANT VIEW, UT, 84414-1665]]
often_linked:
  - MUELLER, NATE
  - [[CAREY, PATRICK]], agent
  - [[MUELLER, NATHAN W]], registered agent, manager
  - Abe J Gleeson, agent
---

[[KELLY NICHOLAS HEITZ, INC. (Utah - 4858667-0142)]]
[[KELLY NICHOLAS HEITZ INC. (Utah - 7558223-0142)]]


```mermaid
C4Context
      title System Context diagram for Internet Banking System
      Enterprise_Boundary(b0, "BankBoundary0") {
        Person(customerA, "Banking Customer A", "A customer of the bank, with personal bank accounts.")
        Person(customerB, "Banking Customer B")
        Person_Ext(customerC, "Banking Customer C", "desc")
    
        Person(customerD, "Banking Customer D", "A customer of the bank, <br/> with personal bank accounts.")
    
        System(SystemAA, "Internet Banking System", "Allows customers to view information about their bank accounts, and make payments.")
    
        Enterprise_Boundary(b1, "BankBoundary") {
    
        SystemDb_Ext(SystemE, "Mainframe Banking System", "Stores all of the core banking information about customers, accounts, transactions, etc.")

        System_Boundary(b2, "BankBoundary2") {
          System(SystemA, "Banking System A")
          System(SystemB, "Banking System B", "A system of the bank, with personal bank accounts. next line.")
        }
    
        System_Ext(SystemC, "E-mail system", "The internal Microsoft Exchange e-mail system.")
        SystemDb(SystemD, "Banking System D Database", "A system of the bank, with personal bank accounts.")
    
        Boundary(b3, "BankBoundary3", "boundary") {
          SystemQueue(SystemF, "Banking System F Queue", "A system of the bank.")
          SystemQueue_Ext(SystemG, "Banking System G Queue", "A system of the bank, with personal bank accounts.")
        }
        }
      }
    
      BiRel(customerA, SystemAA, "Uses")
      BiRel(SystemAA, SystemE, "Uses")
      Rel(SystemAA, SystemC, "Sends e-mails", "SMTP")
      Rel(SystemC, customerA, "Sends e-mails to")
    
      UpdateElementStyle(customerA, $fontColor="red", $bgColor="grey", $borderColor="red")
      UpdateRelStyle(customerA, SystemAA, $textColor="blue", $lineColor="blue", $offsetX="5")
      UpdateRelStyle(SystemAA, SystemE, $textColor="blue", $lineColor="blue", $offsetY="-10")
      UpdateRelStyle(SystemAA, SystemC, $textColor="blue", $lineColor="blue", $offsetY="-40", $offsetX="-50")
      UpdateRelStyle(SystemC, customerA, $textColor="red", $lineColor="red", $offsetX="-50", $offsetY="20")
    
      UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```


# Person Overview - HEITZ, KELLY

## General Data

| Companies                            | Positions          |
|--------------------------------------|-------------------|
| [[MOUNTAIN PRIME LLC (Illinois - LLC_05154839)]]       | manager           |
| [[MPH1, LLC (Illinois - 05211824)]]                 | member            |
| [[CROSS COUNTRY EQUITY, LLC (Utah - 9591953-0160)]]     | manager           |
| [[MOUNTAIN PRIME 2017 LLC BRANCH (Minnesota - cfaaa8a5-1402-e811-9155-00155d0d6f70)]]  | manager           |
| [[ALL SEASONS REAL ESTATE LLC (Utah - 7053375-0160)]]| member, registered agent, agent            |

## Address

| Address Associated                                      |
|-----------------------------------------------|
| [[3138 N 1250 W, PLEASANT VIEW, UT, 84414-1665]]      |

## Other Associated Officers

| Name            | Position          |
|-----------------|-------------------|
| [[MUELLER, NATHAN W]]   | manager           |
| [[CAREY, PATRICK]]   | agent             |
| [[MUELLER, NATHAN W]]  | registered agent  |
| [[GLEESON, ABE J]]   | agent             |

## Last Updated

| Date          |
|---------------|
| 2022-11-11    |

#### other
| KELLY N HEITZ     | Principal | [[ALL SEASONS REAL ESTATE LLC (Utah - 7053375-0160)]] |     |
| --------------- | --------- | --------------------------- | --- |
| Ogden, Utah, US |           |                             |     |
| Location: [[1341 E 2925 N, OGDEN, UT, 84414-1821]]                |           |                             |     |