{
    "name": "Cysar Brand",
    "version": "20.0.1.0.0",
    "category": "Theme",
    "summary": "Interface do Odoo em preto",
    "author": "Cysar",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web._assets_primary_variables": [
            ("prepend", "cysar_brand/static/src/scss/primary_variables.scss"),
        ],
    },
    "installable": True,
}
