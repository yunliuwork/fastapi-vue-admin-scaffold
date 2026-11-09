export interface ThemePalette {
  id: string
  label: string
  accent: string
  ink: string
  menuSub: string
  menuHover: string
  menuText: string
  paper: string
  sheet: string
  line: string
  text: string
  muted: string
  rowAlt: string
  rowHover: string
  headerBg: string
  accentSoft: string
  accountHover: string
  loginHue: string
}

export const palettes: ThemePalette[] = [
  {
    id: 'celadon',
    label: '青瓷',
    accent: '#0E7C74',
    ink: '#163033',
    menuSub: '#102628',
    menuHover: '#1D4548',
    menuText: '#D7E4E2',
    paper: '#F2F5F4',
    sheet: '#FBFCFB',
    line: '#D3DDDB',
    text: '#162326',
    muted: '#5C6C6A',
    rowAlt: '#F3F7F6',
    rowHover: '#EBF1EF',
    headerBg: '#F7FAF9',
    accentSoft: '#EEF6F5',
    accountHover: '#E7EEED',
    loginHue: '0deg',
  },
  {
    id: 'ocean',
    label: '海蓝',
    accent: '#2563C9',
    ink: '#14243D',
    menuSub: '#0F1C31',
    menuHover: '#1C3253',
    menuText: '#D6E1F2',
    paper: '#F2F5FA',
    sheet: '#FBFCFE',
    line: '#D5DDE9',
    text: '#16202E',
    muted: '#556375',
    rowAlt: '#F3F6FB',
    rowHover: '#EAF0F8',
    headerBg: '#F6F9FD',
    accentSoft: '#EDF3FC',
    accountHover: '#E4EBF4',
    loginHue: '45deg',
  },
  {
    id: 'violet',
    label: '墨紫',
    accent: '#6A4C93',
    ink: '#241C33',
    menuSub: '#1B1527',
    menuHover: '#362A4B',
    menuText: '#E2DBEC',
    paper: '#F6F4F8',
    sheet: '#FCFBFD',
    line: '#DDD6E6',
    text: '#201A2A',
    muted: '#5F566C',
    rowAlt: '#F5F2F8',
    rowHover: '#EFEAF5',
    headerBg: '#FAF8FC',
    accentSoft: '#F1ECF7',
    accountHover: '#EAE4F1',
    loginHue: '90deg',
  },
  {
    id: 'ochre',
    label: '赭石',
    accent: '#A85A2A',
    ink: '#33231B',
    menuSub: '#271A13',
    menuHover: '#463225',
    menuText: '#EDE0D6',
    paper: '#F7F3EF',
    sheet: '#FCFAF8',
    line: '#E2D6CA',
    text: '#2A211B',
    muted: '#6C5D52',
    rowAlt: '#F6F1EB',
    rowHover: '#F0E8E0',
    headerBg: '#FAF6F2',
    accentSoft: '#F7EEE6',
    accountHover: '#EBE1D6',
    loginHue: '210deg',
  },
  {
    id: 'snow',
    label: '皓白',
    accent: '#1F2328',
    ink: '#FFFFFF',
    menuSub: '#FAFBFC',
    menuHover: '#F1F3F4',
    menuText: '#3A4247',
    paper: '#F7F8F8',
    sheet: '#FFFFFF',
    line: '#E3E6E8',
    text: '#1B1F22',
    muted: '#656C71',
    rowAlt: '#F7F8F9',
    rowHover: '#EFF2F3',
    headerBg: '#FBFCFC',
    accentSoft: '#F0F2F3',
    accountHover: '#EFF1F2',
    loginHue: '0deg',
  },
]

export const DEFAULT_PALETTE_ID = 'celadon'

export function getPalette(id: string): ThemePalette {
  return palettes.find((palette) => palette.id === id) ?? palettes[0]
}
