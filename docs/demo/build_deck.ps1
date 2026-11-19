$ErrorActionPreference = 'Stop'
$build = Join-Path $PSScriptRoot '.build'
$outDir = Join-Path $build 'pptx'
$out = Join-Path $PSScriptRoot 'ChitMirror_Pitch_Deck.pptx'
if (Test-Path $build) { Remove-Item $build -Recurse -Force }
New-Item -ItemType Directory -Force -Path "$outDir\_rels", "$outDir\docProps", "$outDir\ppt\_rels", "$outDir\ppt\slides\_rels", "$outDir\ppt\slideMasters\_rels", "$outDir\ppt\slideLayouts\_rels", "$outDir\ppt\theme" | Out-Null
function SaveXml($path,$content) { Set-Content -LiteralPath $path -Value $content -Encoding utf8 }
$slides = @(
@{Title='ChitMirror'; Subtitle='From payment chaos to a clearer chit ledger'; Body='Payment claims in conversations. Evidence checked before a ledger status changes.'; Kind='cover'},
@{Title='Payment records are scattered'; Subtitle='One payment may leave three partial records'; Body='CHAT  “Sent for March”
SCREENSHOT  Image in a thread
LEDGER  Manual row to update

Names, months, amounts and proof can be hard to reconcile when the conversation is the record.'},
@{Title='A reviewable path from claim to record'; Subtitle='CONCEPTUAL FLOW — not live in this checkout'; Body='1  Capture: message + image
2  Structure: member · month · amount
3  Compare: independent bank CSV
4  Review: foreman resolves ambiguity
5  Record: status + reason

Extraction, evidence checks and ledger writes are not implemented in this checkout.'},
@{Title='A screenshot is a claim'; Subtitle='EXPECTED SCENARIOS — NOT RESULTS PRODUCED BY THIS BUILD'; Body='MATCHING CREDIT — compare amount and reference to bank CSV
NO BANK MATCH — reference absent from CSV
REUSED REFERENCE — reference already recorded
WRONG AMOUNT — claim differs from expected amount

A screenshot alone never establishes a bank transaction. Independent bank CSV evidence is required. The verifier and scenario assets are not present here.'},
@{Title='Operational rules need backend confirmation'; Subtitle='Late fees, reminders and payout'; Body='LATE FEE  Due date + bank credit time + configured rule (issue #25 pending)
REMINDER  In-app record; no WhatsApp claim (issue #27 pending)
PAYOUT  Keep locked while required verification is missing (issue #26 pending)

No fee, reminder delivery or payout-unlocked result is available in the current repository.'},
@{Title='Separate pages, shared service boundary'; Subtitle='Independent frontends; one intended backend contract'; Body='CHAT UI  Composer + sender picker; requests /state and /message
DASHBOARD  Independent page; currently a T20 placeholder

Current backend: GET /health only. Chat state and message routes are absent.'},
@{Title='Member transparency depends on a reliable record'; Subtitle='Useful member view (conceptual)'; Body='• Month and instalment
• Payment status
• Reason for review
• Applicable fee or dividend

The current dashboard has no member ledger or statement data. This is not a screenshot of a working view.'},
@{Title='Trust comes from evidence and clear limits'; Subtitle='For foremen: less manual reconciliation, clear review reasons'; Body='For members: a status they can understand, backed by independent evidence.

NEXT MILESTONE
Merge the real verification and integration paths, then rehearse every result against the backend.

Current build is an early UI shell; no end-to-end verification is claimed.'}
)
function Esc([string]$s) { return [System.Security.SecurityElement]::Escape($s) }
$slideXmlFiles = @()
for($i=0;$i -lt $slides.Count;$i++) {
  $idx=$i+1; $d=$slides[$i]; $title=Esc $d.Title; $subtitle=Esc $d.Subtitle; $body=Esc $d.Body
  $titleY=690000; $subY=1800000; $bodyY=2650000; $titleSize=3100; $bodySize=1950
  if($idx -eq 1){$titleY=1500000;$titleSize=3900;$subY=3300000;$bodyY=4400000;$bodySize=2250}
  $bodyLines=$d.Body -split "
"; $paras=''; foreach($line in $bodyLines){$paras += "<a:p><a:pPr/><a:r><a:rPr lang=`"en-US`" sz=`"$bodySize`" dirty=`"0`"><a:solidFill><a:srgbClr val=`"2D3323`"/></a:solidFill><a:latin typeface=`"Aptos`"/></a:rPr><a:t>$(Esc $line)</a:t></a:r><a:endParaRPr lang=`"en-US`" sz=`"$bodySize`"/></a:p>"}
  $slide="<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><p:sld xmlns:a=`"http://schemas.openxmlformats.org/drawingml/2006/main`" xmlns:r=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships`" xmlns:p=`"http://schemas.openxmlformats.org/presentationml/2006/main`"><p:cSld name=`"Slide $idx`"><p:bg><p:bgPr><a:solidFill><a:srgbClr val=`"F5F7F5`"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id=`"1`" name=`"`"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x=`"0`" y=`"0`"/><a:ext cx=`"0`" cy=`"0`"/><a:chOff x=`"0`" y=`"0`"/><a:chExt cx=`"0`" cy=`"0`"/></a:xfrm></p:grpSpPr>
  <p:sp><p:nvSpPr><p:cNvPr id=`"2`" name=`"Title`"/><p:cNvSpPr txBox=`"1`"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x=`"620000`" y=`"$titleY`"/><a:ext cx=`"10900000`" cy=`"900000`"/></a:xfrm><a:prstGeom prst=`"rect`"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap=`"square`"/><a:lstStyle/><a:p><a:pPr/><a:r><a:rPr lang=`"en-US`" sz=`"$titleSize`" b=`"1`"><a:solidFill><a:srgbClr val=`"194637`"/></a:solidFill><a:latin typeface=`"Aptos Display`"/></a:rPr><a:t>$title</a:t></a:r><a:endParaRPr lang=`"en-US`" sz=`"$titleSize`"/></a:p></p:txBody></p:sp>
  <p:sp><p:nvSpPr><p:cNvPr id=`"3`" name=`"Subtitle`"/><p:cNvSpPr txBox=`"1`"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x=`"650000`" y=`"$subY`"/><a:ext cx=`"11000000`" cy=`"650000`"/></a:xfrm><a:prstGeom prst=`"rect`"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap=`"square`"/><a:lstStyle/><a:p><a:pPr/><a:r><a:rPr lang=`"en-US`" sz=`"2200`" b=`"1`"><a:solidFill><a:srgbClr val=`"496F24`"/></a:solidFill><a:latin typeface=`"Aptos`"/></a:rPr><a:t>$subtitle</a:t></a:r><a:endParaRPr lang=`"en-US`"/></a:p></p:txBody></p:sp>
  <p:sp><p:nvSpPr><p:cNvPr id=`"4`" name=`"Content`"/><p:cNvSpPr txBox=`"1`"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x=`"650000`" y=`"$bodyY`"/><a:ext cx=`"10900000`" cy=`"3300000`"/></a:xfrm><a:prstGeom prst=`"rect`"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap=`"square`"/><a:lstStyle/>$paras</p:txBody></p:sp>
  <p:sp><p:nvSpPr><p:cNvPr id=`"5`" name=`"Footer`"/><p:cNvSpPr txBox=`"1`"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x=`"620000`" y=`"6500000`"/><a:ext cx=`"10500000`" cy=`"300000`"/></a:xfrm><a:prstGeom prst=`"rect`"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang=`"en-US`" sz=`"1000`" b=`"1`"><a:solidFill><a:srgbClr val=`"5E6D65`"/></a:solidFill><a:latin typeface=`"Aptos`"/></a:rPr><a:t>EARLY BUILD · DEMO LIMITATIONS SHOWN</a:t></a:r></a:p></p:txBody></p:sp>
  </p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
  SaveXml (Join-Path $outDir "ppt\slides\slide$idx.xml") $slide
  SaveXml (Join-Path $outDir "ppt\slides\_rels\slide$idx.xml.rels") '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>'
  $slideXmlFiles += "<Override PartName=`"/ppt/slides/slide$idx.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.slide+xml`"/>"
}
SaveXml (Join-Path $outDir '[Content_Types].xml') "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><Types xmlns=`"http://schemas.openxmlformats.org/package/2006/content-types`"><Default Extension=`"rels`" ContentType=`"application/vnd.openxmlformats-package.relationships+xml`"/><Default Extension=`"xml`" ContentType=`"application/xml`"/><Override PartName=`"/ppt/presentation.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml`"/><Override PartName=`"/ppt/slideMasters/slideMaster1.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml`"/><Override PartName=`"/ppt/slideLayouts/slideLayout1.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml`"/><Override PartName=`"/ppt/theme/theme1.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.theme+xml`"/>$($slideXmlFiles -join '')</Types>"
SaveXml (Join-Path $outDir '_rels\.rels') '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>'
$slideIds='';$rels='';for($i=1;$i -le $slides.Count;$i++){$slideIds += "<p:sldId id=`"$([int](255+$i))`" r:id=`"rId$($i+1)`"/>";$rels += "<Relationship Id=`"rId$($i+1)`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide`" Target=`"slides/slide$i.xml`"/>"}
$rels += '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
SaveXml (Join-Path $outDir 'ppt\presentation.xml') "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><p:presentation xmlns:a=`"http://schemas.openxmlformats.org/drawingml/2006/main`" xmlns:r=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships`" xmlns:p=`"http://schemas.openxmlformats.org/presentationml/2006/main`"><p:sldMasterIdLst><p:sldMasterId id=`"2147483648`" r:id=`"rId1`"/></p:sldMasterIdLst><p:sldIdLst>$slideIds</p:sldIdLst><p:sldSz cx=`"12192000`" cy=`"6858000`" type=`"screen16x9`"/><p:notesSz cx=`"6858000`" cy=`"9144000`"/></p:presentation>"
SaveXml (Join-Path $outDir 'ppt\_rels\presentation.xml.rels') "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><Relationships xmlns=`"http://schemas.openxmlformats.org/package/2006/relationships`">$rels</Relationships>"
SaveXml (Join-Path $outDir 'ppt\slideMasters\slideMaster1.xml') '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap accent1="496F24" accent2="194637" accent3="5E6D65" accent4="A63C34" accent5="E8F1EB" accent6="DCE5DE" bg1="FFFFFF" bg2="F5F7F5" tx1="2D3323" tx2="5E6D65" hlink="0563C1" folHlink="954F72"/><p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="3200"/></a:lvl1pPr></p:titleStyle><p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle><p:otherStyle><a:lvl1pPr><a:defRPr sz="1400"/></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>'
SaveXml (Join-Path $outDir 'ppt\slideMasters\_rels\slideMaster1.xml.rels') '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>'
SaveXml (Join-Path $outDir 'ppt\slideLayouts\slideLayout1.xml') '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
SaveXml (Join-Path $outDir 'ppt\slideLayouts\_rels\slideLayout1.xml.rels') '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>'
SaveXml (Join-Path $outDir 'ppt\theme\theme1.xml') '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="ChitMirror"><a:themeElements><a:clrScheme name="ChitMirror"><a:dk1><a:srgbClr val="2D3323"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="194637"/></a:dk2><a:lt2><a:srgbClr val="F5F7F5"/></a:lt2><a:accent1><a:srgbClr val="496F24"/></a:accent1><a:accent2><a:srgbClr val="A63C34"/></a:accent2><a:accent3><a:srgbClr val="5E6D65"/></a:accent3><a:accent4><a:srgbClr val="DCE5DE"/></a:accent4><a:accent5><a:srgbClr val="E8F1EB"/></a:accent5><a:accent6><a:srgbClr val="68756E"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme></a:themeElements></a:theme>'
SaveXml (Join-Path $outDir 'docProps\core.xml') '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>ChitMirror Pitch Deck</dc:title><dc:creator>ChitMirror</dc:creator><dc:subject>Five-minute product narrative with implementation limitations</dc:subject></cp:coreProperties>'
if(Test-Path -LiteralPath $out){Remove-Item -LiteralPath $out -Force}; python -c "import pathlib,zipfile,sys; root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); z=zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED); [z.write(p,p.relative_to(root).as_posix()) for p in root.rglob('*') if p.is_file()]; z.close()" $outDir $out
Write-Output "Created $out with $($slides.Count) editable slides"
