ALLATOM = "AA"
UNITEDATOM = "UA"
COARSEGRAINED = "CG"
FFTYPE_CHOICES = (
    (ALLATOM, 'All atom'),
    (UNITEDATOM, 'United atom'),
    (COARSEGRAINED, 'Coarse grained')
)

AMBER     = "AM"
CHARMM    = "CH"
GROMACS45 = "GR45"
GROMACS50 = "GR50"
SFTYPE_CHOICES = (
    (AMBER, 'Amber'),
    (CHARMM, 'Charmm'),
    (GROMACS45, 'Gromacs 4.5'),
    (GROMACS50, 'Gromacs 5.0'),
)

