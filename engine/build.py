import json, datetime as dt
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
o=json.load(open('engine_out.json'))
P=lambda s: dt.datetime.fromisoformat(s) if s else None
DT='ddd dd mmm, h AM/PM'; L='#,##0'; LD='#,##0;-#,##0;"–"'
wb=Workbook(); first=True
def sheet(name,head,rows,fmts,widths):
    global first
    ws=wb.active if first else wb.create_sheet(); first=False; ws.title=name
    ws.append(head)
    for r in rows: ws.append(r)
    for c in ws[1]: c.fill=PatternFill('solid',fgColor='F3F3F3'); c.alignment=Alignment(wrap_text=True,vertical='bottom')
    for col,f in fmts.items():
        for row in ws.iter_rows(min_row=2,min_col=col,max_col=col):
            for c in row: c.number_format=f
    for i,w in enumerate(widths): ws.column_dimensions[chr(65+i)].width=w
    ws.freeze_panes='B2'
fly=[[r[0],r[1],P(r[2]),P(r[3]),r[4],r[5],r[6],r[7],P(r[8]),r[9],P(r[10]),P(r[11]),P(r[12]),r[13]] for r in o['fly']]
sheet('POM to Aiambak',["Vessel","Voy #","Depart POM","ETA Aiambak","CFO (L)","Transferred to","To river vessels (L)","To Amigo 1 (L)","ETA Kiunga (river)","Lead time POM→Kiunga (days)","Load start POM","Depart Aiambak","ETA POM (return)","Extra wait at Aiambak (h)"],fly,
      {3:DT,4:DT,5:L,7:LD,8:LD,9:DT,10:'0.0',11:DT,12:DT,13:DT,14:'0;-0;"–"'},[16,7,22,22,12,30,13,13,22,13,22,22,22,12])
riv=[[r[0],r[1],r[2],P(r[3]),P(r[4]),P(r[5]),r[6],P(r[7])] for r in o['river']]
sheet('Aiambak to Kiunga',["Vessel","Loaded at","Loaded from","Load start","Depart","ETA Kiunga","CFO (L)","ETA Aiambak (return)"],riv,{4:DT,5:DT,6:DT,7:L,8:DT},[14,11,30,22,22,22,12,22])
am=[[dt.datetime.fromisoformat(r[0]),r[1],r[2],r[3],r[4],r[5],r[6]] for r in o['amigo']]
sheet('Amigo 1',["Date","CFO in (L)","Trucked out (L)","Closing stock (L)","Waiting aboard Fly vessels (L)","Vessels arriving","River vessels loading"],am,{1:'ddd dd mmm',2:LD,3:LD,4:L,5:LD},[14,13,13,14,15,30,30])
st=[[dt.datetime.fromisoformat(r[0]),r[1],r[2],r[3],r[4],r[5],r[6],r[7]] for r in o['site']]
sheet('Kiunga Site',["Date","River arrivals (L)","Truck arrivals (L)","Site use (L)","Closing stock (L)","Days of fuel","Status","Lowest during day (L)"],st,{1:'ddd dd mmm',2:LD,3:LD,4:LD,5:'#,##0;[Red]-#,##0',6:'0.0;[Red]-0.0',8:'#,##0;[Red]-#,##0'},[14,14,14,13,15,10,34,15])
for ws in wb: 
    for c in ws[1]: c.font=Font(bold=False)
wb.save('schedule_sim.xlsx'); print([ws.title for ws in wb], [ws.max_row for ws in wb])
