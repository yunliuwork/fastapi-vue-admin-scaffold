import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#0E7C74',
    colorInfo: '#0E7C74',
    colorLink: '#0E7C74',
    borderRadius: 8,
    fontFamily: '"IBM Plex Sans", "PingFang SC", "Microsoft YaHei", sans-serif',
    colorBgLayout: '#F2F5F4',
    colorText: '#162326',
    colorTextSecondary: '#5C6C6A',
    colorBorder: '#D3DDDB',
    controlHeight: 36,
  },
  components: {
    Menu: {
      colorItemBg: '#163033',
      colorSubItemBg: '#102628',
      colorItemBgSelected: '#0E7C74',
      colorItemBgHover: '#1D4548',
      colorItemText: '#D7E4E2',
      colorItemTextHover: '#F7FBFA',
      colorItemTextSelected: '#F7FBFA',
    },
    Layout: {
      colorBgHeader: '#F7FAF9',
      colorBgBody: '#F2F5F4',
    },
  },
}
