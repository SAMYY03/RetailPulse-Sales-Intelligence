param([int]$Port = 45119, [switch]$Apply, [switch]$Portfolio)
$ErrorActionPreference = 'Stop'
Add-Type -Path 'D:\bi\bin\Microsoft.AnalysisServices.Server.Core.dll'
Add-Type -Path 'D:\bi\bin\Microsoft.AnalysisServices.Server.Tabular.dll'
Add-Type -Path 'D:\bi\bin\Microsoft.PowerBI.AdomdClient.dll'
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$Port")
$db = $server.Databases[0]
$model = $db.Model
$table = $model.Tables.Find('measures (2)')
if (!$table -or !$model.Tables.Find('FactSales')) { throw 'Unexpected model; no changes made.' }
$definitions = @(
    @('Revenue', 'SUM(FactSales[Price])', '\$#,0.00;(\$#,0.00);\$0.00', 'Item prices excluding freight, across all order statuses in the current sales-item selection.'),
    @('Freight Revenue', 'SUM(FactSales[FreightValue])', '\$#,0.00;(\$#,0.00);\$0.00', 'Freight charged on selected sales items; this is not freight profit.'),
    @('Total Order Value', '[Revenue] + [Freight Revenue]', '\$#,0.00;(\$#,0.00);\$0.00', 'Item prices plus freight for selected sales items; not a payment reconciliation measure.'),
    @('Orders', 'DISTINCTCOUNT(FactSales[OrderID])', '#,0', 'Distinct orders with sales items in the current selection. Orders without items are excluded.'),
    @('Units Sold', 'COUNTROWS(FactSales)', '#,0', 'Sales-item rows in the current selection, including all order statuses.'),
    @('Customers', 'COUNTROWS(FILTER(SUMMARIZE(FactSales, DimCustomer[customer_unique_id]), NOT ISBLANK(DimCustomer[customer_unique_id])))', '#,0', 'Distinct people with selected sales items, using the persistent customer_unique_id. Respects date, product, customer and order filters.'),
    @('AOV', 'COALESCE(DIVIDE([Revenue], [Orders]), 0)', '\$#,0.00;(\$#,0.00);\$0.00', 'Average selected merchandise value per order, excluding freight. Returns zero when there are no orders.'),
    @('AOV Including Freight', 'COALESCE(DIVIDE([Total Order Value], [Orders]), 0)', '\$#,0.00;(\$#,0.00);\$0.00', 'Average selected item value plus freight per order. Returns zero when there are no orders.'),
    @('Units per Order', 'COALESCE(DIVIDE([Units Sold], [Orders]), 0)', '0.00', 'Average selected sales-item count per order. Returns zero when there are no orders.'),
    @('Revenue per Customer', 'COALESCE(DIVIDE([Revenue], [Customers]), 0)', '\$#,0.00;(\$#,0.00);\$0.00', 'Selected merchandise revenue per distinct person, excluding freight.'),
    @('Repeat Customers', 'COUNTROWS(FILTER(ADDCOLUMNS(FILTER(SUMMARIZE(FactSales, DimCustomer[customer_unique_id]), NOT ISBLANK(DimCustomer[customer_unique_id])), "@OrderCount", CALCULATE([Orders])), [@OrderCount] > 1))', '#,0', 'People with more than one distinct order within the current selection, not lifetime repeat buyers.'),
    @('Repeat Customer Rate', 'COALESCE(DIVIDE([Repeat Customers], [Customers]), 0)', '0.0%', 'Share of customers with more than one selected order. Returns zero for an empty selection.')
)
if ($Apply) {
    if ($Portfolio) {
        $definitions += @(Get-Content 'powerbi\portfolio-kpis.json' -Raw | ConvertFrom-Json)
        $datePartition = $model.Tables.Find('DimDate').Partitions[0]
        $datePartition.Source.Expression = $datePartition.Source.Expression.Replace('MIN(FactSales[OrderDate])', 'DATE(YEAR(MIN(FactSales[OrderDate])), 1, 1)').Replace('MAX(FactSales[OrderDate])', 'DATE(YEAR(MAX(FactSales[OrderDate])), 12, 31)')
        $model.Tables.Find('DimDate').RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
    }
    foreach ($d in $definitions) {
        $measure = $table.Measures.Find($d[0])
        if (!$measure) { $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure; $measure.Name = $d[0]; $table.Measures.Add($measure) }
        $measure.Expression = $d[1]
        $measure.FormatString = $d[2]
        $measure.Description = $d[3]
        if ($d.Count -gt 4) { $measure.DisplayFolder = $d[4] }
    }
    $model.Tables.Find('DimDate').Columns.Find('Month Name').SortByColumn = $model.Tables.Find('DimDate').Columns.Find('Month Number')
    $model.SaveChanges() | Out-Null
}
$connection = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection "Data Source=localhost:$Port"
$connection.Open()
function Query([string]$Dax) {
    $command = $connection.CreateCommand(); $command.CommandText = $Dax
    $reader = $command.ExecuteReader()
    $rows = @()
    while ($reader.Read()) {
        $record = [ordered]@{}
        for ($i=0; $i -lt $reader.FieldCount; $i++) { $record[$reader.GetName($i)] = if ($reader.IsDBNull($i)) { $null } else { $reader.GetValue($i) } }
        $rows += [pscustomobject]$record
    }
    $reader.Close()
    return $rows
}
$pairs = ($table.Measures | ForEach-Object { '"' + $_.Name + '", [' + $_.Name + ']' }) -join ', '
$contexts = [ordered]@{
    total = ''
    year2017 = 'TREATAS({2017}, DimDate[Year])'
    year2018 = 'TREATAS({2018}, DimDate[Year])'
    month201807 = 'TREATAS({"2018-07"}, DimDate[Year Month])'
    stateSP = 'TREATAS({"SP"}, DimCustomer[State])'
    category = 'TREATAS({"bed_bath_table"}, DimProdut[category])'
    delivered = 'TREATAS({"delivered"}, Orders[order_status])'
    canceled = 'TREATAS({"canceled"}, Orders[order_status])'
    combined = 'TREATAS({2017}, DimDate[Year]), TREATAS({"SP"}, DimCustomer[State]), TREATAS({"bed_bath_table"}, DimProdut[category])'
    empty = 'TREATAS({1900}, DimDate[Year])'
}
$results = [ordered]@{}
foreach ($entry in $contexts.GetEnumerator()) {
    $body = "ROW($pairs)"
    if ($entry.Value) { $body = "CALCULATETABLE($body, $($entry.Value))" }
    $results[$entry.Key] = @(Query "EVALUATE $body")[0]
}
$results | ConvertTo-Json -Depth 6 | Set-Content 'outputs\measure-results.json'
if ($Portfolio) {
    $exports = [ordered]@{}
    $exports.monthly = @(Query ('EVALUATE SUMMARIZECOLUMNS(DimDate[Year Month], ' + $pairs + ') ORDER BY DimDate[Year Month]'))
    $exports.categories = @(Query ('EVALUATE SUMMARIZECOLUMNS(DimProdut[category], TREATAS({"2018-07"}, DimDate[Year Month]), ' + $pairs + ')'))
    $exports.states = @(Query ('EVALUATE SUMMARIZECOLUMNS(DimCustomer[State], TREATAS({"2018-07"}, DimDate[Year Month]), ' + $pairs + ')'))
    $exports | ConvertTo-Json -Depth 8 | Set-Content 'outputs\portfolio-kpi-export.json'
}
[Microsoft.AnalysisServices.Tabular.JsonSerializer]::SerializeDatabase($db) | Set-Content 'outputs\model-after.json'
$table.Measures | ForEach-Object { "// $($_.Description)`n$($_.Name) = $($_.Expression)`n" } | Set-Content 'powerbi\measures.dax'
$results.total | ConvertTo-Json
$connection.Close(); $server.Disconnect()

