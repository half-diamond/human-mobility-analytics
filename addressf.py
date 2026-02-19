import overpy
from shapely.geometry import Point, Polygon , LineString
import math
import pyproj
import pandas as pd
from tqdm import tqdm
import decimal
from alive_progress import alive_bar
geod = pyproj.Geod(ellps='WGS84')
class Map:
    class zone:
        def __init__ (self):
            self.relations = []
            self.closed_ways = []
            self.road_ways = []
    def __init__ (self,path,no_of_zones = 1000):
        api = overpy.Overpass()
        with open(path,"r",encoding="utf-8") as file:
            print("Loadeding map ... ")
            self.map_data = api.parse_xml(data= file.read() ,encoding='utf-8', parser=None)
        self.grid = []
        for i in range(no_of_zones):
            row = []
            for j in range(no_of_zones):
                row.append(self.zone())
            self.grid.append(row)
        self.no_of_zones = no_of_zones
        self.ln ,self.lx,self.lox,self.lon= 1000,0,0, 1000
        for no in self.map_data.nodes:
            self.ln  = min(self.ln  , no.lat)
            self.lx  = max(self.lx  , no.lat)
            self.lox = max(self.lox , no.lon)
            self.lon = min(self.lon , no.lon)
        self.yx ,self.yy= (self.lx - self.ln)/1000 , (self.lox - self.lon)/1000
        print("Extracting relations ...")
        self.progress_bar = tqdm(total= ( len(self.map_data.relations) ), desc="Progress ", position=0)

        self.extract_relations()
        self.progress_bar.close()
        print("Extracting ways ...")
        self.extract_ways()

    def extract_relations(self):
        for relation in self.map_data.relations:
            self.progress_bar.update(1)
            if relation.tags.get('name') == None or relation.tags.get('type') not in ['boundary', 'site', 'multipolygon'] or relation.tags.get('name') == "City" or relation.id in [9511877,9511845,9511878]:
                continue
            closed_ways = []
            unclosed_ways = []
            breaker = False
            for member in relation.members:
                if type(member) == overpy.RelationWay:
                    resolved_way = None
                    try:
                        resolved_way = member.resolve()
                    except overpy.exception.DataIncomplete as e:
                        breaker = True
                        break
                    if resolved_way.nodes[0].id == resolved_way.nodes[-1].id:
                        closed_ways.append(member.resolve().nodes)
                    else:
                        unclosed_ways.append(member.resolve().nodes)
            if breaker == True:
                continue
            i = 0
            while i < len(unclosed_ways):
                current_way = unclosed_ways[i]
                if current_way[0] == current_way[-1]:
                    closed_ways.append(current_way)
                    del unclosed_ways[i]
                    continue
                j = i + 1
                while j < len(unclosed_ways):
                    way = unclosed_ways[j]
                    nway = []
                    if current_way[0] == way[0]:
                        current_way.reverse()
                        nway = current_way + way
                        del unclosed_ways[i]
                        del unclosed_ways[j-1]
                        unclosed_ways.append(nway)
                        i -= 1
                        break
                    if current_way[0] == way[-1]:
                        nway = way + current_way
                        del unclosed_ways[i]
                        del unclosed_ways[j-1]
                        unclosed_ways.append(nway)
                        i -= 1
                        break
                    j += 1
                i += 1
            
            for way in closed_ways:
                lats = []
                lons = []
                if type(way) != list:
                    way = way.nodes
                for nod in way:
                    lats.append(nod.lat)
                    lons.append(nod.lon)
                row_min, col_min = int((min(lats) - self.ln) // self.yx), int((min(lons) - self.lon) // self.yy)
                row_max, col_max = int((max(lats) - self.ln) // self.yx), int((max(lons) - self.lon) // self.yy)
                for row in range(row_min, row_max+1):
                    for col in range(col_min, col_max + 1):
                        listt = []
                        for nod in way:
                            listt.append((float(nod.lat),float(nod.lon)))
                        polygon = Polygon(listt).convex_hull                        
                        self.grid[row][col].relations.append((polygon, relation.tags))                
        for row in range(row_min, row_max+1):
            for col in range(col_min, col_max + 1):
                        self.grid[row][col].relations.sort(key = lambda x: x[0].area)

    def extract_ways(self):
        for way in self.map_data.ways:
            lats =[]
            lons =[]
            if way.nodes[0] == way.nodes[-1]:
                for nod in way.nodes:
                    lats.append(nod.lat)
                    lons.append(nod.lon)
                row_min ,col_min =int((min(lats) - self.ln)//self.yx) , int((min(lons) - self.lon)//self.yy)
                row_max ,col_max =int((max(lats) - self.ln)//self.yx) , int((max(lons) - self.lon)//self.yy)
                listt = []
                for nod in way.nodes:
                    listt.append((float(nod.lat),float(nod.lon)))
                polygon = Polygon(listt).convex_hull
                for row in range(row_min,row_max+1):
                    for col in range(col_min, col_max + 1):
                        self.grid[row][col].closed_ways.append((polygon, way.tags))
                        self.grid[row][col].closed_ways.sort(key = lambda x: x[0].area)
                        
                        
                    
            else:               
                line = LineString([(nod.lat , nod.lon) for nod in way.nodes])
                p1 = line.parallel_offset(0.0002)
                p2 = line.parallel_offset(-0.0002)
                vertices = [pp for pp in p1.coords] + [pp for pp in reversed(p2.coords)]
                po = Polygon(vertices)
                for nod in po.exterior.coords:
                    lats.append(decimal.Decimal(nod[0]))
                    lons.append(decimal.Decimal(nod[1]))
                row_min ,col_min =int((min(lats) - self.ln)//self.yx) , int((min(lons) - self.lon)//self.yy)
                row_max ,col_max =int((max(lats) - self.ln)//self.yx) , int((max(lons) - self.lon)//self.yy)
                for row in range(row_min,row_max+1):
                    for col in range(col_min, col_max + 1):
                        if row == self.no_of_zones:
                            row = self.no_of_zones - 1
                        if col == self.no_of_zones:
                            col = self.no_of_zones - 1
                        self.grid[row][col].road_ways.append((po, way.tags))  

    def relation_query(self,lat, longg):
        point = Point((lat,longg))
        row , col = int((lat - float(self.ln))//float(self.yx)) , int((longg - float(self.lon))//float(self.yy))
        wl = []
        for poly , tags in self.grid[row][col].relations:
            if poly.contains(point):
                wl.append(tags)
        return wl
    
    def p_query (self,lat,longg):
        point = Point((lat,longg))
        row , col = int((lat - float(self.ln))//float(self.yx)) , int((longg - float(self.lon))//float(self.yy))
        for polygon, tags in reversed(self.grid[row][col].closed_ways):
            if polygon.contains(point):
                return tags
        return None
    
    def q2 (self,lat ,longg):
        point = Point((lat,longg))
        row , col = int((lat - float(self.ln))//float(self.yx)) , int((longg - float(self.lon))//float(self.yy))
        for polygon, tags in reversed(self.grid[row][col].road_ways):
            if tags.get("name") == None:
                continue
            if polygon.contains(point):
                return tags
        return {}
        nway = None
        row , col = int((lat - float(self.ln))//float(self.yx)) , int((longg - float(self.lon))//float(self.yy))
        ways = self.grid[row][col].road_ways
        if len(ways) == 1:
            return ways[0].tags
        elif len(ways) == 0:
            return {}
        else:
            md = 100000
            for way in ways:
                dis = 100000
                if (way.nodes[0].lat-way.nodes[-1].lat) == 0:
                    dis = abs(lat - float(way.nodes[0].lat))
                else :
                    m = float((way.nodes[0].lon-way.nodes[-1].lon)/(way.nodes[0].lat-way.nodes[-1].lat))
                    c = float(way.nodes[0].lon) - float(way.nodes[0].lat) * m
                    dis = abs(m*lat - longg + c)/math.sqrt(1+ m**2)
                if dis < md:
                    md = dis
                    nway = way
            return nway.tags
    def find_location(self, lat, longg):
        df = {}
        if lat<self.ln or lat> self.lx or longg<self.lon or longg>self.lox:
            df["is_outside"] = 1
            return df
        else:
            df["is_outside"] = 0
        rel = self.relation_query(lat,longg)
        cnt = 0
        # for i,el in enumerate(rel):
        #     if el.get("type") in ["site","multipolygon"]:
        #         temp = rel.pop(i)
        #         rel = [temp] + rel
        
        for tag in reversed(rel):
            if cnt == 3 :
                df["area1"] = ", ".join([i.get("name") for i in rel[:len(rel)-3]])
                break
            df[f"area{4-cnt}"] = tag.get("name") if tag.get("name:en") == None else tag.get("name:en")
            cnt += 1
        if len(rel) == 0:
            a1 = self.p_query(lat,longg)
            a2 = self.q2(lat,longg)
            if a1 != None:
                a2 = a1
            df["name"] = a2.get("name") if a2.get("name:en") == None else a2.get("name:en")
            for typ in ["amenity","tourism","historic","leisure","man_made","shop","building","military","landuse"]:
                if typ == "building" and a2.get(typ) == "yes":
                    continue
                if a2.get(typ) != None:
                    df["type"] = a2.get(typ)
                    break
            if df.get("type") == None and a2.get("highway") != None:
                df["type"] = "road"
            if df.get("type") == None and a2.get("railway") != None:
                df["type"] = "rail_line"
        elif rel[0].get("type") == "boundary":
            a1 = self.p_query(lat,longg)
            a2 = self.q2(lat,longg)
            if a1 != None:
                a2 = a1
            df["name"] = a2.get("name") if a2.get("name:en") == None else a2.get("name:en")
            for typ in ["amenity","tourism","historic","leisure","man_made","shop","building","military","landuse"]:
                if typ == "building" and a2.get(typ) == "yes":
                    continue
                if a2.get(typ) != None:
                    df["type"] = a2.get(typ)
                    break
            if df.get("type") == None and a2.get("highway") != None:
                df["type"] = "road"
            if df.get("type") == None and a2.get("railway") != None:
                df["type"] = "rail_line"
        elif rel[0].get("type") in ["site","multipolygon"]:
            df["name"] = rel[0].get("name") if rel[0].get("name:en") == None else rel[0].get("name:en")
            for typ in ["amenity","tourism","historic","leisure","man_made","shop","building","military","landuse"]:
                if typ == "building" and rel[0].get(typ) == "yes":
                    continue
                if rel[0].get(typ) != None:
                    df["type"] = rel[0].get(typ)
                    break
        return df
    def process_file(self,filename,name):
        df = pd.read_csv(filename, usecols=["lat","long","path number","velocity","datetime"])
        res = []
        i = 0
        typ =[]
        nam =[]
        a1=[]
        a2 =[]
        a3=[]
        a4 = []
        iso = []
        with alive_bar(len(df),force_tty = True,bar = "bubbles",spinner = "dots_waves") as bar:
            for id in df.index.values:
                ans = self.find_location(df.iloc[id]['lat'], df.iloc[id]['long'])
                iso.append(ans.get("is_outside"))
                typ.append(ans.get("type"))
                nam.append(ans.get("name"))
                a1.append(ans.get("area1"))
                a2.append(ans.get("area2"))
                a3.append(ans.get("area3"))
                a4.append(ans.get("area4"))
                bar()
        df["name"]= nam
        df["type"]= typ
        df["area1"]= a1
        df["area2"]= a2
        df["area3"]= a3
        df["area4"]= a4
        df["is_outside"] = iso
        df.to_csv(f"out\\{name}", index=False)
        return res

