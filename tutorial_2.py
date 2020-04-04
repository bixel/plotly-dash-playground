import json

import numpy as np
import awkward
import boost_histogram as bh

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


data = awkward.load('./Bs2DsPi_2018_Chunk.awkd')
hist = bh.Histogram(
    bh.axis.Regular(1000, 4800, 7000, metadata=dict(var='lab0__M')),
    bh.axis.Regular(1000, 1900, 2100, metadata=dict(var='lab2_M')),
)
hist.fill(data['lab0__M'], data['lab2_M'])
variable_map = {meta['var']: i for i, meta in enumerate(hist.axes.metadata)}

binning = 1


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Hello Interactive Analysis!'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    html.Label('Rebin'),
    dcc.Slider(
        id='binning-slider',
        min=1,
        max=100,
        value=10,
        marks={i: f'{i}' for i in range(10, 100, 10)}
    ),

    html.Div(children=[
        dcc.Graph(
            id='lab0__M-graph',
            figure={}
        ),
    ]),

    html.Div(children=[
        dcc.Graph(
            id='lab2_M-graph',
            figure={}
        ),
    ]),

    html.Pre(id='selected-data'),
])


def update_histogram(variable, rebin, ranges):
    global hist, variable_map

    slices = tuple([
        slice(
            bh.loc(min) if min is not None else None,
            bh.loc(max) if max is not None else None,
            bh.sum if i != variable_map[variable] else None
        )
        for i, (min, max) in enumerate(ranges)
    ])

    summed_hist = hist.project(variable_map[variable])[::bh.rebin(rebin)]
    selected_hist = hist[slices][::bh.rebin(rebin)]

    return {
        'data': [
            {
                'x': summed_hist.axes.centers[0],
                'y': summed_hist.view(),
                'width': summed_hist.axes.widths[0],
                'type': 'bar',
                'name': 'Raw',
            },
            {
                'x': selected_hist.axes.centers[0],
                'y': selected_hist.view(),
                'width': selected_hist.axes.widths[0],
                'type': 'bar',
                'name': 'Selected',
            },
        ],
        'layout': {
            'title': 'Dash Data Visualization',
            'xaxis': {
                'title': 'm(hhhh) / MeV',
            },
            'yaxis': {
                'title': f'Entries / {summed_hist.axes.widths[0][0]:.2f} MeV'
            },
            'barmode': 'overlay',
            'clickmode': 'event+select',
        },
    }


@app.callback(
    [
        Output(component_id='lab0__M-graph', component_property='figure'),
        Output(component_id='lab2_M-graph', component_property='figure'),
        Output(component_id='selected-data', component_property='children'),
    ],
    [
        Input(component_id='binning-slider', component_property='value'),
        Input(component_id='lab0__M-graph', component_property='selectedData'),
        Input(component_id='lab2_M-graph', component_property='selectedData'),
    ]
)
def printSelectedData(binning, *selectedData):
    ranges = []
    for sel in selectedData:
        if sel is not None and 'points' in sel:
            points = sel['points']
            points = [p for p in points if p['curveNumber'] == 0]
            if points:
                ranges.append(
                    (
                        float(points[0]['x']),
                        float(points[-1]['x']) + float(points[-1]['width'])
                    )
                )
            else:
                ranges.append((None, None))
        else:
            ranges.append((None, None))
    return (
        update_histogram('lab0__M', rebin=binning, ranges=ranges),
        update_histogram('lab2_M', rebin=binning, ranges=ranges),
        json.dumps(selectedData, indent=2)
    )


if __name__ == '__main__':
    app.run_server(debug=True)
