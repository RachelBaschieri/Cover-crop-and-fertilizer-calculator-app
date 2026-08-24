from app import cover_crop_analysis, material_results, operation_cost

def close(a,b,tol=1e-6): assert abs(a-b)<tol, (a,b)

def test_workbook_cover_crop_example():
    r=cover_crop_analysis(8,4.64,3.2,15)
    close(r['fresh_lb_ac'],25264.8)
    close(r['dry_lb_ac'],3789.72)
    close(r['total_n_lb_ac'],121.27104)
    close(r['pan4_lb_ac'],43.4902203648)
    close(r['pan10_lb_ac'],52.862046336)

def test_chicken_manure_example():
    _,t=material_results([{'name':'Chicken manure - dried (4-3-2)','rate':3500,'price':.25}])
    close(t['cost'],875)
    close(t['total_n'],140)
    close(t['pan4'],56.823529413)
    close(t['pan10'],77.823529413)
    close(t['p2o5'],105)
    close(t['k2o'],70)

def test_drill_example():
    r=operation_cost({'method':'drill','tractor_hp':70,'fuel_price':4,'labor_rate':15,'width_ft':10,'speed_mph':3})
    close(r['acres_hr'],3.0920334667)
    close(r['fuel_gal_hr'],3.08)
    close(r['tractor_cost_hr'],8.75)

    close(r['total_cost_ac'],16.7874170762)
