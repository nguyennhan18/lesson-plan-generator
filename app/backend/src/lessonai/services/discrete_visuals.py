"""Finite numeric constructions: no supplied polygon or executable expression."""
import math


def number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>1e6:
        raise ValueError('Số liệu phải hữu hạn, trị tuyệt đối không quá 1.000.000')
    return float(value)


def normalize(data):
    kind=data['kind']
    if kind=='arithmetic_sequence':
        first=number(data['first_term']);difference=number(data['common_difference']);count=data['count']
        if isinstance(count,bool) or not isinstance(count,int) or not 1<=count<=200:raise ValueError('Số số hạng từ 1 đến 200')
        return {'kind':kind,'first_term':first,'common_difference':difference,'count':count}
    if kind=='inequality_system':
        constraints=data['constraints']
        if not isinstance(constraints,list) or not 1<=len(constraints)<=12:raise ValueError('Cần từ 1 đến 12 bất phương trình')
        rows=[]
        for row in constraints:
            if not isinstance(row,dict):raise ValueError("Bất phương trình không đúng cấu trúc")
            a,b,c=[number(row.get(key)) for key in ('a','b','c')]
            if a==0 and b==0:raise ValueError('Ít nhất một hệ số a hoặc b phải khác 0')
            relation=row.get('relation')
            if relation not in ('<=','>=','<','>'):raise ValueError('Quan hệ bất phương trình không hợp lệ')
            rows.append({'a':a,'b':b,'c':c,'relation':relation})
        window={key:number(data[key]) for key in ('x_min','x_max','y_min','y_max')}
        if window['x_min']>=window['x_max'] or window['y_min']>=window['y_max']:raise ValueError('Cửa sổ hiển thị không hợp lệ')
        return {'kind':kind,'constraints':rows,**window}
    raise ValueError('Chưa hỗ trợ kiểu biểu diễn này')


def construct(data):
    spec=normalize(data)
    if spec['kind']=='arithmetic_sequence':
        return {'points':[[n,spec['first_term']+(n-1)*spec['common_difference']] for n in range(1,spec['count']+1)]}
    xmin,xmax,ymin,ymax=[spec[key] for key in ('x_min','x_max','y_min','y_max')]
    polygon=[[xmin,ymin],[xmax,ymin],[xmax,ymax],[xmin,ymax]]
    for row in spec['constraints']:
        sign=-1 if row['relation'] in ('>=','>') else 1
        a,b,c=[row[key]*sign for key in ('a','b','c')]
        output=[]
        for i,p in enumerate(polygon):
            q=polygon[(i+1)%len(polygon)];fp=a*p[0]+b*p[1]-c;fq=a*q[0]+b*q[1]-c
            if fp<=0:output.append(p)
            if (fp<=0)!=(fq<=0):
                t=fp/(fp-fq);output.append([p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])])
        polygon=output
        if not polygon:break
    return {'polygon':polygon,'constraints':spec['constraints'],'scope':'Miền nghiệm trong cửa sổ hiển thị; biên nét đứt không thuộc miền nghiệm.'}
