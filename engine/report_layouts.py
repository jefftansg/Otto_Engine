"""Versioned layout tokens derived from supplied reference formatting, never client values."""
LAYOUTS = {
 'classic-v1': dict(name='Otto classic (legacy)', title=17, heading=12, body=9, table=7.3,
                    font='Helvetica', accent='#152641', approved=False),
 'reference-compact-v1': dict(name='Reference compact sans', title=16, heading=11, body=8.5, table=8.5,
                    font='Helvetica', accent='#000000', approved=False),
 'reference-standard-v1': dict(name='Reference standard sans', title=14, heading=11, body=10, table=9.5,
                    font='Helvetica', accent='#2C638A', approved=False),
}


def layout(config, kind):
    key=config.get('report_layout_'+kind,'classic-v1')
    if key not in LAYOUTS:
        raise ValueError('Unknown report layout revision. Select a supported layout.')
    return key,LAYOUTS[key]
