Attribute VB_Name = "FieldReportImport"
' Loads FieldReport section text into the active document.
'
' Each section in <template>.fields.txt starts with a line ===FIELD:name===.
' The text is placed into, in order of preference:
'   1. content controls whose Tag equals the field name, or
'   2. a bookmark with the same name.
' The template's own macros, styles, and layout are not touched.
' Fields with no matching control or bookmark are listed at the end.
Option Explicit

Public Sub ImportFieldReport()
    Dim path As Variant
    path = PickFile()
    If path = False Then Exit Sub

    Dim fields As Object
    Set fields = ParseFields(ReadUtf8(CStr(path)))

    Dim name As Variant, missing As String, placed As Boolean
    For Each name In fields.Keys
        placed = FillContentControls(CStr(name), fields(name))
        If Not placed Then placed = FillBookmark(CStr(name), fields(name))
        If Not placed Then missing = missing & vbCrLf & "  - " & name
    Next name

    If Len(missing) > 0 Then
        MsgBox "Imported. No content control or bookmark found for:" & missing, vbInformation, "FieldReport"
    Else
        MsgBox "Imported all sections.", vbInformation, "FieldReport"
    End If
End Sub

Private Function PickFile() As Variant
    With Application.FileDialog(msoFileDialogFilePicker)
        .Title = "Choose a FieldReport .fields.txt file"
        .Filters.Clear
        .Filters.Add "FieldReport fields", "*.fields.txt"
        If .Show = -1 Then PickFile = .SelectedItems(1) Else PickFile = False
    End With
End Function

Private Function ReadUtf8(path As String) As String
    Dim stm As Object
    Set stm = CreateObject("ADODB.Stream")
    stm.Type = 2: stm.Charset = "utf-8": stm.Open
    stm.LoadFromFile path
    ReadUtf8 = stm.ReadText
    stm.Close
End Function

Private Function ParseFields(text As String) As Object
    Dim d As Object: Set d = CreateObject("Scripting.Dictionary")
    Dim lines() As String: lines = Split(Replace(text, vbCrLf, vbLf), vbLf)
    Dim i As Long, cur As String, buf As String
    For i = LBound(lines) To UBound(lines)
        If Left$(lines(i), 9) = "===FIELD:" And Right$(lines(i), 3) = "===" Then
            If Len(cur) > 0 Then d(cur) = TrimNewlines(buf)
            cur = Mid$(lines(i), 10, Len(lines(i)) - 12)
            buf = ""
        ElseIf Len(cur) > 0 Then
            buf = buf & lines(i) & vbCr
        End If
    Next i
    If Len(cur) > 0 Then d(cur) = TrimNewlines(buf)
    Set ParseFields = d
End Function

Private Function TrimNewlines(s As String) As String
    Do While Right$(s, 1) = vbCr: s = Left$(s, Len(s) - 1): Loop
    TrimNewlines = s
End Function

Private Function FillContentControls(tag As String, value As String) As Boolean
    Dim cc As ContentControl
    For Each cc In ActiveDocument.SelectContentControlsByTag(tag)
        cc.Range.Text = value
        FillContentControls = True
    Next cc
End Function

Private Function FillBookmark(name As String, value As String) As Boolean
    If Not ActiveDocument.Bookmarks.Exists(name) Then Exit Function
    Dim r As Range
    Set r = ActiveDocument.Bookmarks(name).Range
    r.Text = value
    ActiveDocument.Bookmarks.Add name, r   ' re-create so a second import replaces the text
    FillBookmark = True
End Function
