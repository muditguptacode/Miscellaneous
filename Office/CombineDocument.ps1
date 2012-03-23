$word = New-Object -ComObject word.application
$word.visible = $false
$infile = "D:\Test\test.docx"
$DocumentPath = "D:\Test\Final.docx"
$doc = $word.documents.open($infile)
 $p = $doc.Paragraphs.Item($doc.Paragraphs.Count) 
 $p.Range.InsertParagraphAfter()
 $p.PageBreakBefore = -1

$doc.SaveAs([Ref]$DocumentPath)
$doc.close()
$word.Quit()
[gc]::collect()
[gc]::WaitForPendingFinalizers()