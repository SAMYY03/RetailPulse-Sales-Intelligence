"""Build the native Power BI report using Microsoft's documented PBIR format."""
import json
import zipfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'powerbi'
REPORT = BASE / 'RetailPulse.Report'
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/'
NAVY, TEAL, BG, MUTED = '#172D46', '#087F8C', '#F2F5F8', '#5F7185'

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')

def lit(value):
    if isinstance(value, bool): value = str(value).lower()
    elif isinstance(value, str): value = "'" + value.replace("'", "''") + "'"
    else: value = str(value) + 'D'
    return {'expr': {'Literal': {'Value': value}}}

def color(value): return {'solid': {'color': lit(value)}}
def obj(**properties): return [{'properties': properties}]
def field(table, prop, measure=False):
    return {'Measure' if measure else 'Column': {'Expression': {'SourceRef': {'Entity': table}}, 'Property': prop}}
def projection(table, prop, measure=False):
    return {'field': field(table, prop, measure), 'queryRef': f'{table}.{prop}', 'nativeQueryRef': prop}
def metric(name): return projection('measures (2)', name, True)

def container(title='', background=True):
    return {
        'title': obj(show=lit(bool(title)), text=lit(title), fontColor=color(NAVY), fontSize=lit(12), fontFamily=lit('Segoe UI Semibold')),
        'background': obj(show=lit(background), color=color('#FFFFFF'), transparency=lit(0)),
        'border': obj(show=lit(False)),
        'visualHeader': obj(show=lit(False)),
    }

page_ids = []
visual_manifest = []
def visual(page, name, kind, x,y,w,h, title='', roles=None, objects=None, sort=None):
    data = {'$schema': SCHEMA+'definition/visualContainer/2.6.0/schema.json', 'name': name,
            'position': {'x':x,'y':y,'z':len(visual_manifest)*1000,'width':w,'height':h,'tabOrder':len(visual_manifest)},
            'visual': {'visualType':kind,'visualContainerObjects':container(title), 'drillFilterOtherVisuals':True}}
    if roles:
        data['visual']['query']={'queryState':{role:{'projections':p} for role,p in roles.items()}}
        if sort: data['visual']['query']['sortDefinition']={'sort':[{'field':sort[0],'direction':sort[1]}]}
    if objects: data['visual']['objects']=objects
    write(REPORT/'definition'/'pages'/page/'visuals'/name/'visual.json',data)
    visual_manifest.append({'page':page,'name':name,'kind':kind,'title':title,'x':x,'y':y,'width':w,'height':h})
    return data

def text(page,name,value,x,y,w,h,size=12,colour=MUTED):
    visual(page,name,'textbox',x,y,w,h,objects={'general':obj(paragraphs=[{'textRuns':[{'value':value,'textStyle':{'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':colour}}]}])})
    p=REPORT/'definition'/'pages'/page/'visuals'/name/'visual.json'
    data=json.loads(p.read_text(encoding='utf-8')); data['visual']['visualContainerObjects']=container('',False); write(p,data)

def slicer(page,name,table,column,x,w,default=None):
    props={'mode':lit('Dropdown')}
    objects={'data':obj(**props),'header':obj(show=lit(False)), 'items':obj(fontColor=color(NAVY),textSize=lit(11))}
    if default is not None:
        val=str(default)+'L' if isinstance(default,int) else "'"+default+"'"
        objects['general']=obj(filter={'filter':{'Version':2,'From':[{'Name':'d','Entity':table,'Type':0}], 'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'d'}},'Property':column}}], 'Values':[[{'Literal':{'Value':val}}]]}}}]}})
    data=visual(page,name,'slicer',x,26,w,66,column,{'Values':[projection(table,column)]},objects)
    data['visual']['syncGroup']={'groupName':column,'fieldChanges':True,'filterChanges':True}
    write(REPORT/'definition'/'pages'/page/'visuals'/name/'visual.json',data)

def page(pid,title,subtitle):
    page_ids.append(pid)
    write(REPORT/'definition'/'pages'/pid/'page.json',{'$schema':SCHEMA+'definition/page/2.0.0/schema.json','name':pid,'displayName':title,'displayOption':'FitToPage','height':800,'width':1280,'objects':{'background':obj(color=color(BG),transparency=lit(0))}})
    text(pid,'heading',title,24,16,660,45,25,NAVY)
    text(pid,'subtitle',subtitle,26,64,740,27,10)
    slicer(pid,'year','DimDate','Year',804,130,2018)
    slicer(pid,'month','DimDate','Month Name',946,145)
    slicer(pid,'state','DimCustomer','State',1103,153)
    text(pid,'footer','RETAILPULSE AI  /  Olist historical data 2016–2018  •  2018 is incomplete  •  Revenue includes all statuses; excludes freight',24,768,1232,25,9)

def cards(pid,names):
    gap=12; w=(1232-gap*(len(names)-1))/len(names)
    for n,name in enumerate(names):
        units=1000000 if name=='Revenue' else 1000 if name in ('Orders','Customers','Repeat Customers') else 1
        visual(pid,f'kpi{n}','card',24+n*(w+gap),112,w,100,roles={'Values':[metric(name)]},objects={'labels':obj(color=color(NAVY),fontSize=lit(27),labelDisplayUnits=lit(units),labelPrecision=lit(1 if units>1 or 'Rate' in name or '%' in name or 'Days' in name else 2)), 'categoryLabels':obj(show=lit(True),color=color(MUTED),fontSize=lit(10))})

def chart(pid,name,kind,table,column,measures,box,title,chronological=False):
    objects={'legend':obj(show=lit(len(measures)>1)), 'categoryAxis':obj(showAxisTitle=lit(False),fontSize=lit(10),labelColor=color(MUTED)), 'valueAxis':obj(showAxisTitle=lit(False),fontSize=lit(10),labelColor=color(MUTED)), 'dataPoint':obj(defaultColor=color(TEAL)), 'labels':obj(show=lit(False))}
    visual(pid,name,kind,*box,title,{'Category':[projection(table,column)],'Y':[metric(m) for m in measures]},objects,(field(table,column) if chronological else field('measures (2)',measures[0],True),'Ascending' if chronological else 'Descending'))

def table(pid,name,dimension,measures,box,title):
    visual(pid,name,'tableEx',*box,title,{'Values':[projection(*dimension)]+[metric(m) for m in measures]}, {'grid':obj(gridVertical=lit(False),gridHorizontal=lit(True),rowPadding=lit(7)), 'columnHeaders':obj(fontColor=color(NAVY),backColor=color('#E9EFF4'),fontSize=lit(10)), 'values':obj(fontColorPrimary=color(NAVY),fontSize=lit(10)), 'total':obj(totals=lit(True))},(field('measures (2)',measures[0],True),'Descending'))

write(BASE/'RetailPulse.pbip',{'version':'1.0','artifacts':[{'report':{'path':'RetailPulse.Report'}}],'settings':{'enableAutoRecovery':True}})
write(BASE/'RetailPulse.SemanticModel'/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'4.0','settings':{}})
write(REPORT/'definition.pbir',{'$schema':SCHEMA+'definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../RetailPulse.SemanticModel'}}})
write(REPORT/'definition'/'version.json',{'$schema':SCHEMA+'definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
for folder,kind in [(REPORT,'Report'),(BASE/'RetailPulse.SemanticModel','SemanticModel')]:
    if not (folder/'.platform').exists():
        write(folder/'.platform',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json','metadata':{'type':kind,'displayName':'RetailPulse'},'config':{'version':'2.0','logicalId':str(uuid.uuid4())}})
with zipfile.ZipFile(ROOT/'frjkt.pbix') as z:
    path=REPORT/'StaticResources'/'SharedResources'/'BaseThemes'/'CY26SU02.json'; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(z.read('Report/StaticResources/SharedResources/BaseThemes/CY26SU02.json'))
write(REPORT/'definition'/'report.json',{'$schema':SCHEMA+'definition/report/3.1.0/schema.json','themeCollection':{'baseTheme':{'name':'CY26SU02','type':'SharedResources','reportVersionAtImport':{'visual':'2.6.0','report':'3.1.0','page':'2.0.0'}}},'resourcePackages':[{'name':'SharedResources','type':'SharedResources','items':[{'name':'CY26SU02','path':'BaseThemes/CY26SU02.json','type':'BaseTheme'}]}], 'settings':{'useStylableVisualContainerHeader':True,'defaultDrillFilterOtherVisuals':True,'useEnhancedTooltips':True,'allowChangeFilterTypes':True},'objects':{'outspacePane':obj(expanded=lit(False))}})

page('executive','Executive Overview','Sales performance  /  Select a year for a meaningful prior-year comparison')
cards('executive',['Revenue','Orders','Customers','AOV','YoY Revenue Growth %'])
chart('executive','revenue_trend','lineChart','DimDate','Year Month',['Revenue','Revenue PY'],(24,232,748,252),'Revenue and prior year by month',True)
chart('executive','state_revenue','barChart','DimCustomer','State',['Revenue'],(788,232,468,252),'State contribution • scroll to explore')
chart('executive','category_revenue','barChart','DimProdut','category',['Revenue'],(24,500,620,252),'Category revenue • scroll to explore')
chart('executive','orders_trend','clusteredColumnChart','DimDate','Year Month',['Orders'],(660,500,596,252),'Orders by month',True)

page('customers','Product & Customer Analysis','Basket value and repeat purchasing  /  Repeat customers are measured within your selection')
cards('customers',['Customers','Repeat Customers','Repeat Customer Rate','Revenue per Customer'])
chart('customers','category_units','barChart','DimProdut','category',['Units Sold'],(24,232,480,330),'Category demand • sales items')
table('customers','category_detail',('DimProdut','category'),['Revenue','Orders','AOV','Repeat Customer Rate'],(520,232,736,520),'Category performance • click a row to filter')
chart('customers','customer_trend','lineChart','DimDate','Year Month',['Customers'],(24,578,480,174),'Customer trend',True)

page('drivers','Performance Drivers','Growth and customer experience  /  Delivery and review metrics give each order equal weight')
cards('drivers',['YoY Revenue Growth %','Late Delivery Rate','Average Delivery Days','Average Review Score'])
chart('drivers','state_growth','barChart','DimCustomer','State',['YoY Revenue Change'],(24,232,600,238),'Revenue change by state • versus prior year')
chart('drivers','category_growth','barChart','DimProdut','category',['YoY Revenue Change'],(640,232,616,238),'Revenue change by category • versus prior year')
table('drivers','experience',('DimProdut','category'),['Delivery Eligible Orders','Late Delivery Rate','Reviewed Orders','Average Review Score'],(24,486,1232,266),'Customer experience by category • late rate uses eligible deliveries only')
write(REPORT/'definition'/'pages'/'pages.json',{'$schema':SCHEMA+'definition/pagesMetadata/1.0.0/schema.json','pageOrder':page_ids,'activePageName':'executive'})
write(ROOT/'outputs'/'dashboard-manifest.json',visual_manifest)
print(f'Built {len(page_ids)} pages and {len(visual_manifest)} native visuals.')
