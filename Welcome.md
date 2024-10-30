The highlights of evidence is located in [[proceedings/parties/plaintiff/evidence/evidence|The `Evidence` folder]]
```dataview
LIST without ID 
FROM "proceedings" 
FLATTEN parties
GROUP BY parties
WHERE length(parties) > 0  
```