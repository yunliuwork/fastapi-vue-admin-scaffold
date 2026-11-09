<script setup lang="ts">
import { nextTick, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import { useSessionStore } from '@/stores/session'
import { registerAccessRoutes } from '@/router/access'

type Step = 'credentials' | 'totp_verify' | 'totp_bind'

const router = useRouter()
const route = useRoute()
const session = useSessionStore()
const loading = ref(false)
const showSeed = import.meta.env.DEV
const step = ref<Step>('credentials')
const preAuthToken = ref('')
const bindSecret = ref('')
const qrCanvas = ref<HTMLCanvasElement | null>(null)
const form = reactive({ username: '', password: '', totp_code: '' })

const rules = {
  username: [{ required: true, message: '请填写用户名' }],
  password: [{ required: true, message: '请填写密码' }],
  totp_code: [{ required: true, message: '请填写 6 位验证码', pattern: /^\d{6}$/ }],
}

async function renderQr(url: string) {
  await nextTick()
  if (qrCanvas.value) {
    await QRCode.toCanvas(qrCanvas.value, url, { width: 200, margin: 1 })
  }
}

async function enterApp() {
  registerAccessRoutes(router, session.menus)
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  await router.push(redirect)
}

async function submitCredentials() {
  loading.value = true
  try {
    const result = await session.signInWithPassword(form.username, form.password)
    if (result.login_step === 'complete') {
      await session.completeLogin(result.access_token, result.refresh_token)
      await enterApp()
      return
    }
    preAuthToken.value = result.pre_auth_token
    form.totp_code = ''
    if (result.login_step === 'totp_verify') {
      step.value = 'totp_verify'
      return
    }
    bindSecret.value = result.secret
    step.value = 'totp_bind'
    await renderQr(result.otpauth_url)
  } catch {
    session.clear()
  } finally {
    loading.value = false
  }
}

async function submitTotp() {
  if (!/^\d{6}$/.test(form.totp_code.trim())) {
    return
  }
  loading.value = true
  try {
    if (step.value === 'totp_verify') {
      await session.verifyTotpAndLogin(preAuthToken.value, form.totp_code.trim())
    } else {
      await session.bindTotpAndLogin(preAuthToken.value, form.totp_code.trim())
    }
    await enterApp()
  } catch {
    session.clear()
    step.value = 'credentials'
    preAuthToken.value = ''
    bindSecret.value = ''
  } finally {
    loading.value = false
  }
}

function backToCredentials() {
  step.value = 'credentials'
  preAuthToken.value = ''
  bindSecret.value = ''
  form.totp_code = ''
}

</script>

<template>
  <main class="login">
    <section class="card" :class="{ wide: step === 'totp_bind' }">
      <header class="intro">
        <p class="product">fastapi-vue-admin-scaffold</p>
        <p class="tagline">FastAPI + Vue 3 管理端脚手架</p>
      </header>
      <h1>{{ step === 'credentials' ? '登录' : step === 'totp_verify' ? '谷歌验证' : '绑定谷歌验证器' }}</h1>

      <a-form
        v-if="step === 'credentials'"
        :model="form"
        :rules="rules"
        layout="vertical"
        @finish="submitCredentials"
      >
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="form.username" size="large" autocomplete="username" />
        </a-form-item>
        <a-form-item label="密码" name="password">
          <a-input-password
            v-model:value="form.password"
            size="large"
            autocomplete="current-password"
          />
        </a-form-item>
        <a-button type="primary" html-type="submit" size="large" :loading="loading" block>
          下一步
        </a-button>
      </a-form>

      <template v-else-if="step === 'totp_verify'">
        <p class="hint">账号 <b>{{ form.username }}</b> 已启用谷歌验证，请输入 App 中的 6 位数字。</p>
        <a-form :model="form" :rules="rules" layout="vertical" @finish="submitTotp">
          <a-form-item label="验证码" name="totp_code">
            <a-input
              v-model:value="form.totp_code"
              size="large"
              maxlength="6"
              inputmode="numeric"
              autocomplete="one-time-code"
              placeholder="6 位数字"
            />
          </a-form-item>
          <a-space direction="vertical" style="width: 100%">
            <a-button type="primary" html-type="submit" size="large" :loading="loading" block>
              进入后台
            </a-button>
            <a-button size="large" block @click="backToCredentials">返回</a-button>
          </a-space>
        </a-form>
      </template>

      <template v-else>
        <p class="hint">
          账号 <b>{{ form.username }}</b> 须先绑定 Google Authenticator。请用手机扫描下方二维码，或手动输入密钥。
        </p>
        <div class="qr-wrap">
          <canvas ref="qrCanvas" aria-label="谷歌验证器绑定二维码" />
        </div>
        <p class="secret">密钥：<code>{{ bindSecret }}</code></p>
        <a-form :model="form" :rules="rules" layout="vertical" @finish="submitTotp">
          <a-form-item label="输入 App 中的 6 位验证码" name="totp_code">
            <a-input
              v-model:value="form.totp_code"
              size="large"
              maxlength="6"
              inputmode="numeric"
              autocomplete="one-time-code"
              placeholder="6 位数字"
            />
          </a-form-item>
          <a-space direction="vertical" style="width: 100%">
            <a-button type="primary" html-type="submit" size="large" :loading="loading" block>
              完成绑定并进入
            </a-button>
            <a-button size="large" block @click="backToCredentials">返回</a-button>
          </a-space>
        </a-form>
      </template>

      <p v-if="showSeed && step === 'credentials'" class="seed">
        种子账号 <b>admin</b>，密码 <b>admin123</b>
      </p>
    </section>
  </main>
</template>

<style scoped>
.login {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 32px 20px;
  overflow: hidden;
  background-color: var(--ink);
}

.login::before {
  position: absolute;
  inset: 0;
  background: url('../../assets/login-bg.svg') center / cover no-repeat;
  content: '';
  filter: hue-rotate(var(--login-hue));
}

.card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 36px 32px 28px;
  border-radius: 12px;
  background: var(--sheet);
}

.card.wide {
  max-width: 440px;
}

.intro {
  text-align: center;
}

.product {
  margin: 0;
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
}

.tagline {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.intro::after {
  content: '';
  display: block;
  width: 36px;
  height: 3px;
  margin: 14px auto 0;
  border-radius: 2px;
  background: var(--accent);
}

h1 {
  margin: 18px 0 24px;
  font-size: 28px;
  font-weight: 600;
}

.hint {
  margin: 0 0 16px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}

.hint b {
  color: var(--text);
}

.qr-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.secret {
  margin: 0 0 16px;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-all;
}

.secret code {
  padding: 2px 6px;
  border-radius: 6px;
  background: var(--paper);
}

.seed {
  margin: 20px 0 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--paper);
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.seed b {
  color: var(--text);
  font-weight: 600;
}
</style>
