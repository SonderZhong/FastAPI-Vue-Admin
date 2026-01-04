<template>
  <div class="page-content user">
    <div class="content">
      <div class="left-wrap">
        <!-- 用户信息卡片 -->
        <div class="user-wrap">
          <div class="profile-header">
            <img class="bg" src="@imgs/user/bg.webp" />
            <div class="avatar-section">
              <div class="avatar-wrapper" @click="triggerAvatarUpload">
                <img class="avatar" :src="getAvatarUrl(userInfo.avatar)" />
                <div class="avatar-overlay">
                  <i class="iconfont-sys">&#xe665;</i>
                  <span>更换头像</span>
                </div>
                <div class="status-indicator"></div>
              </div>
              <!-- 隐藏的文件选择器 -->
              <input
                ref="avatarInputRef"
                type="file"
                accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                style="display: none"
                @change="handleAvatarChange"
              />
            </div>
          </div>

          <div class="profile-info">
            <h2 class="name">{{ userInfo.nickname || userInfo.username }}</h2>
            <p class="position">{{ userInfo.department_name || '暂无部门' }}</p>

            <div class="quick-stats">
              <div class="stat-item">
                <span class="stat-number">{{ formatDate(userInfo.created_at || '') }}</span>
                <span class="stat-label">加入时间</span>
              </div>
            </div>
          </div>

          <div class="outer-info">
            <div class="info-item">
              <i class="iconfont-sys">&#xe72e;</i>
              <span>{{ userInfo.email || '未设置邮箱' }}</span>
            </div>
            <div class="info-item">
              <i class="iconfont-sys">&#xe608;</i>
              <span>{{ getGenderText(userInfo.gender) }}</span>
            </div>
            <div class="info-item">
              <i class="iconfont-sys">&#xe6f5;</i>
              <span>{{ userInfo.phone || '未设置手机号' }}</span>
            </div>
            <div class="info-item">
              <i class="iconfont-sys">&#xe811;</i>
              <span>{{ userInfo.department_name || '暂无部门' }}</span>
            </div>
          </div>
        </div>

        <!-- 快捷导航卡片 -->
        <div class="quick-nav">
          <div class="nav-header">
            <h3>快捷导航</h3>
          </div>
          <div class="nav-items">
            <div class="nav-item" @click="goToMyNotification">
              <div class="nav-icon notification-icon">
                <i class="iconfont-sys">&#xe6c2;</i>
              </div>
              <div class="nav-content">
                <h4>我的通知</h4>
                <p>查看系统通知</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
            <div class="nav-item" @click="goToLoginRecord">
              <div class="nav-icon login-icon">
                <i class="iconfont-sys">&#xe6e0;</i>
              </div>
              <div class="nav-content">
                <h4>登录记录</h4>
                <p>查看登录历史</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
            <div class="nav-item" @click="goToOperationRecord">
              <div class="nav-icon operation-icon">
                <i class="iconfont-sys">&#xe694;</i>
              </div>
              <div class="nav-content">
                <h4>操作记录</h4>
                <p>查看操作日志</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
          </div>
        </div>
      </div>

      <div class="right-wrap">
        <!-- 基本信息设置 -->
        <div class="info">
          <div class="section-header">
            <h1 class="title">
              <i class="iconfont-sys">&#xe7ae;</i>
              基本信息
            </h1>
            <el-button
              type="primary"
              @click="handleBasicInfoEdit"
              :loading="basicInfoLoading"
            >
              <el-icon v-if="!basicInfoLoading" class="mr-1">
                <Check v-if="isEdit" />
                <Edit v-else />
              </el-icon>
              {{ isEdit ? '保存' : '编辑' }}
            </el-button>
          </div>

          <ElForm
            :model="form"
            class="form"
            ref="ruleFormRef"
            :rules="rules"
            label-width="100px"
            label-position="left"
          >
            <div class="form-grid">
              <ElFormItem label="用户名" prop="realName">
                <el-input v-model="form.realName" :disabled="!isEdit" placeholder="请输入用户名">
                  <template #prefix>
                    <i class="iconfont-sys">&#xe7fc;</i>
                  </template>
                </el-input>
              </ElFormItem>
              <ElFormItem label="昵称" prop="nikeName">
                <ElInput v-model="form.nikeName" :disabled="!isEdit" placeholder="请输入昵称">
                  <template #prefix>
                    <i class="iconfont-sys">&#xe7ae;</i>
                  </template>
                </ElInput>
              </ElFormItem>

              <ElFormItem label="性别" prop="sex">
                <ElSelect v-model="form.sex" placeholder="请选择性别" :disabled="!isEdit">
                  <template #prefix>
                    <i class="iconfont-sys">&#xe608;</i>
                  </template>
                  <ElOption
                    v-for="item in genderOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </ElSelect>
              </ElFormItem>

              <ElFormItem label="手机号" prop="mobile">
                <ElInput v-model="form.mobile" :disabled="!isEdit" placeholder="请输入手机号">
                  <template #prefix>
                    <i class="iconfont-sys">&#xe6f5;</i>
                  </template>
                </ElInput>
              </ElFormItem>
            </div>

            <ElFormItem label="个人介绍" prop="des">
              <ElInput
                type="textarea"
                :rows="4"
                v-model="form.des"
                :disabled="!isEdit"
                placeholder="请输入个人介绍"
                show-word-limit
                maxlength="200"
              />
            </ElFormItem>
          </ElForm>
        </div>

        <!-- 安全设置 -->
        <div class="info security-section">
          <div class="section-header">
            <h1 class="title">
              <i class="iconfont-sys">&#xe6da;</i>
              安全设置
            </h1>
          </div>

          <div class="security-items">
            <!-- 修改密码 -->
            <div class="security-item">
              <div class="security-info">
                <div class="security-icon password-icon">
                  <i class="iconfont-sys">&#xe6da;</i>
                </div>
                <div class="security-content">
                  <h3>登录密码</h3>
                  <p>定期更新密码，保护账户安全</p>
                </div>
              </div>
              <el-button type="primary" plain @click="showPasswordDialog = true">
                修改密码
              </el-button>
            </div>

            <!-- 修改邮箱 -->
            <div class="security-item">
              <div class="security-info">
                <div class="security-icon email-icon">
                  <i class="iconfont-sys">&#xe72e;</i>
                </div>
                <div class="security-content">
                  <h3>绑定邮箱</h3>
                  <p>{{ userInfo.email || '未绑定邮箱' }}</p>
                </div>
              </div>
              <el-button type="success" plain @click="showEmailDialog = true">
                {{ userInfo.email ? '修改邮箱' : '绑定邮箱' }}
              </el-button>
            </div>

            <!-- 修改手机号 -->
            <div class="security-item">
              <div class="security-info">
                <div class="security-icon phone-icon">
                  <i class="iconfont-sys">&#xe6f5;</i>
                </div>
                <div class="security-content">
                  <h3>绑定手机</h3>
                  <p>{{ userInfo.phone || '未绑定手机号' }}</p>
                </div>
              </div>
              <el-button type="warning" plain @click="showPhoneDialog = true">
                {{ userInfo.phone ? '修改手机' : '绑定手机' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="450px"
      :close-on-click-modal="false"
    >
      <ElForm :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="100px">
        <ElFormItem label="当前密码" prop="oldPassword">
          <ElInput
            v-model="pwdForm.oldPassword"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </ElFormItem>
        <ElFormItem label="新密码" prop="newPassword">
          <ElInput
            v-model="pwdForm.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </ElFormItem>
        <ElFormItem label="确认密码" prop="confirmPassword">
          <ElInput
            v-model="pwdForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPasswordDialog = false">取消</el-button>
          <el-button type="primary" @click="handlePasswordUpdate" :loading="passwordLoading">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改邮箱对话框 -->
    <el-dialog
      v-model="showEmailDialog"
      title="修改邮箱"
      width="450px"
      :close-on-click-modal="false"
    >
      <ElForm :model="emailForm" :rules="emailRules" ref="emailFormRef" label-width="100px">
        <ElFormItem label="当前密码" prop="password">
          <ElInput
            v-model="emailForm.password"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </ElFormItem>
        <ElFormItem label="新邮箱" prop="email">
          <ElInput v-model="emailForm.email" placeholder="请输入新邮箱地址" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEmailDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEmailUpdate" :loading="emailLoading">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改手机号对话框 -->
    <el-dialog
      v-model="showPhoneDialog"
      title="修改手机号"
      width="450px"
      :close-on-click-modal="false"
    >
      <ElForm :model="phoneForm" :rules="phoneRules" ref="phoneFormRef" label-width="100px">
        <ElFormItem label="当前密码" prop="password">
          <ElInput
            v-model="phoneForm.password"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </ElFormItem>
        <ElFormItem label="新手机号" prop="phone">
          <ElInput v-model="phoneForm.phone" placeholder="请输入新手机号" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPhoneDialog = false">取消</el-button>
          <el-button type="primary" @click="handlePhoneUpdate" :loading="phoneLoading">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { useRouter } from 'vue-router'
  import { useUserStore } from '@/store/modules/user'
  import { ElForm, FormInstance, FormRules, ElMessage, ElLoading } from 'element-plus'
  import { Edit, Check } from '@element-plus/icons-vue'
  import {
    updateUserPassword,
    updateUserEmail,
    updateUserPhone,
    updateBaseUserInfo,
    fetchGetUserInfo
  } from '@/api/auth'
  import { uploadAvatar } from '@/api/system/file'
  import { getAvatarUrl } from '@/utils'

  defineOptions({ name: 'UserCenter' })

  const router = useRouter()
  const userStore = useUserStore()
  const userInfo = computed(() => userStore.getUserInfo)

  // 状态管理
  const isEdit = ref(false)
  const basicInfoLoading = ref(false)
  const passwordLoading = ref(false)
  const emailLoading = ref(false)
  const phoneLoading = ref(false)

  // 对话框显示状态
  const showPasswordDialog = ref(false)
  const showEmailDialog = ref(false)
  const showPhoneDialog = ref(false)

  // 表单引用
  const ruleFormRef = ref<FormInstance>()
  const pwdFormRef = ref<FormInstance>()
  const emailFormRef = ref<FormInstance>()
  const phoneFormRef = ref<FormInstance>()
  const avatarInputRef = ref<HTMLInputElement>()

  // 基本信息表单
  const form = reactive({
    realName: '',
    nikeName: '',
    email: '',
    mobile: '',
    address: '',
    sex: '',
    des: ''
  })

  // 密码表单
  const pwdForm = reactive({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  // 邮箱表单
  const emailForm = reactive({
    password: '',
    email: ''
  })

  // 手机号表单
  const phoneForm = reactive({
    password: '',
    phone: ''
  })

  // 监听用户信息变化，更新表单
  watch(
    () => userStore.getUserInfo,
    (newUserInfo) => {
      if (newUserInfo) {
        form.realName = newUserInfo.username || ''
        form.nikeName = newUserInfo.nickname || ''
        form.email = newUserInfo.email || ''
        form.mobile = newUserInfo.phone || ''
        form.sex = newUserInfo.gender !== undefined ? newUserInfo.gender.toString() : ''
      }
    },
    { immediate: true }
  )

  // 表单验证规则
  const rules = reactive<FormRules>({
    realName: [
      { required: true, message: '请输入姓名', trigger: 'blur' },
      { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    nikeName: [
      { required: true, message: '请输入昵称', trigger: 'blur' },
      { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    mobile: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }],
    sex: [{ required: true, message: '请选择性别', trigger: 'change' }]
  })

  // 密码验证规则
  const pwdRules = reactive<FormRules>({
    oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
    newPassword: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
    ],
    confirmPassword: [
      { required: true, message: '请确认新密码', trigger: 'blur' },
      {
        validator: (rule: any, value: any, callback: any) => {
          if (value !== pwdForm.newPassword) {
            callback(new Error('两次输入密码不一致'))
          } else {
            callback()
          }
        },
        trigger: 'blur'
      }
    ]
  })

  // 邮箱验证规则
  const emailRules = reactive<FormRules>({
    password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
    email: [
      { required: true, message: '请输入邮箱地址', trigger: 'blur' },
      { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
    ]
  })

  // 手机号验证规则
  const phoneRules = reactive<FormRules>({
    password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
    phone: [
      { required: true, message: '请输入手机号', trigger: 'blur' },
      { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
    ]
  })

  // 性别选项
  const genderOptions = [
    { value: '0', label: '未知' },
    { value: '1', label: '男' },
    { value: '2', label: '女' }
  ]

  // 根据性别代码获取性别文本
  const getGenderText = (gender: number | undefined): string => {
    if (gender === undefined) return '未知'
    const genderMap: Record<number, string> = {
      0: '未知',
      1: '男',
      2: '女'
    }
    return genderMap[gender] || '未知'
  }

  // 格式化日期
  const formatDate = (dateStr: string): string => {
    if (!dateStr) return '未知'
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN')
  }

  // 处理基本信息编辑
  const handleBasicInfoEdit = async () => {
    if (isEdit.value) {
      // 保存基本信息
      if (!ruleFormRef.value) return

      try {
        const valid = await ruleFormRef.value.validate()
        if (!valid) return

        basicInfoLoading.value = true

        await updateBaseUserInfo({
          name: form.nikeName,
          gender: parseInt(form.sex)
        })

        // 用户信息会自动更新

        ElMessage.success('基本信息更新成功')
        isEdit.value = false
      } catch (error: any) {
        ElMessage.error(error.response?.data?.msg || '更新失败')
      } finally {
        basicInfoLoading.value = false
      }
    } else {
      isEdit.value = true
    }
  }

  // 处理密码更新
  const handlePasswordUpdate = async () => {
    if (!pwdFormRef.value) return

    try {
      const valid = await pwdFormRef.value.validate()
      if (!valid) return

      passwordLoading.value = true

      await updateUserPassword({
        oldPassword: pwdForm.oldPassword,
        newPassword: pwdForm.newPassword
      })

      ElMessage.success('密码修改成功')
      showPasswordDialog.value = false

      // 重置表单
      pwdForm.oldPassword = ''
      pwdForm.newPassword = ''
      pwdForm.confirmPassword = ''
    } catch (error: any) {
      ElMessage.error(error.response?.data?.msg || '密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  }

  // 处理邮箱更新
  const handleEmailUpdate = async () => {
    if (!emailFormRef.value) return

    try {
      const valid = await emailFormRef.value.validate()
      if (!valid) return

      emailLoading.value = true

      await updateUserEmail({
        password: emailForm.password,
        email: emailForm.email
      })

      // 用户信息会自动更新

      ElMessage.success('邮箱修改成功')
      showEmailDialog.value = false

      // 重置表单
      emailForm.password = ''
      emailForm.email = ''
    } catch (error: any) {
      ElMessage.error(error.response?.data?.msg || '邮箱修改失败')
    } finally {
      emailLoading.value = false
    }
  }

  // 处理手机号更新
  const handlePhoneUpdate = async () => {
    if (!phoneFormRef.value) return

    try {
      const valid = await phoneFormRef.value.validate()
      if (!valid) return

      phoneLoading.value = true

      await updateUserPhone({
        password: phoneForm.password,
        phone: phoneForm.phone
      })

      // 用户信息会自动更新

      ElMessage.success('手机号修改成功')
      showPhoneDialog.value = false

      // 重置表单
      phoneForm.password = ''
      phoneForm.phone = ''
    } catch (error: any) {
      ElMessage.error(error.response?.data?.msg || '手机号修改失败')
    } finally {
      phoneLoading.value = false
    }
  }

  // 跳转到登录记录页
  const goToLoginRecord = () => {
    router.push('/personal-login-record')
  }

  // 跳转到操作记录页
  const goToOperationRecord = () => {
    router.push('/personal-operation-record')
  }

  // 跳转到我的通知页
  const goToMyNotification = () => {
    router.push('/my-notification')
  }

  // 触发头像上传
  const triggerAvatarUpload = () => {
    avatarInputRef.value?.click()
  }

  // 处理头像文件选择
  const handleAvatarChange = async (event: Event) => {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]

    if (!file) return

    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      ElMessage.error('仅支持 JPG、PNG、GIF、WEBP 格式的图片')
      target.value = ''
      return
    }

    // 验证文件大小（限制为 5MB）
    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      ElMessage.error('图片大小不能超过 5MB')
      target.value = ''
      return
    }

    // 显示加载提示
    const loading = ElLoading.service({
      lock: true,
      text: '正在上传头像...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    try {
      // 调用上传接口
      const response = await uploadAvatar(file, userInfo.value?.id)

      // response.data 包含后端返回的 { file_id, file_url, file_size, file_type }
      if (response && response.data && response.data.file_url) {
        // 重新获取用户信息并更新到store
        const userInfoResponse = await fetchGetUserInfo()
        if (userInfoResponse && userInfoResponse.data) {
          userStore.setUserInfo(userInfoResponse.data)
        }

        ElMessage.success('头像更新成功')
      } else {
        ElMessage.error('头像上传失败，请重试')
      }
    } catch (error: any) {
      console.error('头像上传失败:', error)
      ElMessage.error(error.msg || '头像上传失败，请重试')
    } finally {
      loading.close()
      // 清空input的值，以便可以重复选择同一文件
      target.value = ''
    }
  }
</script>

<style lang="scss">
  .user {
    .icon {
      width: 1.4em;
      height: 1.4em;
      overflow: hidden;
      vertical-align: -0.15em;
      fill: currentcolor;
    }
  }
</style>

<style lang="scss" scoped>
  .page-content {
    .content {
      display: flex;
      gap: 20px;
      height: 100%;

      .left-wrap {
        width: 300px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        gap: 20px;

        .user-wrap {
          padding: 0;
          border-radius: 12px;
          overflow: hidden;
          background: var(--el-bg-color);

          .profile-header {
            position: relative;
            height: 120px;

            .bg {
              width: 100%;
              height: 100%;
              object-fit: cover;
            }

            .avatar-section {
              position: absolute;
              bottom: -30px;
              left: 50%;
              transform: translateX(-50%);

              .avatar-wrapper {
                position: relative;
                cursor: pointer;
                transition: transform 0.3s ease;

                &:hover {
                  transform: scale(1.05);

                  .avatar-overlay {
                    opacity: 1;
                  }
                }

                .avatar {
                  width: 60px;
                  height: 60px;
                  object-fit: cover;
                  border: 3px solid white;
                  border-radius: 50%;
                  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                  display: block;
                }

                .avatar-overlay {
                  position: absolute;
                  top: 0;
                  left: 0;
                  width: 60px;
                  height: 60px;
                  border-radius: 50%;
                  background: rgba(0, 0, 0, 0.6);
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  justify-content: center;
                  opacity: 0;
                  transition: opacity 0.3s ease;

                  i {
                    font-size: 16px;
                    color: #fff;
                    margin-bottom: 2px;
                  }

                  span {
                    font-size: 10px;
                    color: #fff;
                    font-weight: 500;
                  }
                }

                .status-indicator {
                  position: absolute;
                  bottom: 5px;
                  right: 5px;
                  width: 12px;
                  height: 12px;
                  background: var(--el-color-success);
                  border: 2px solid white;
                  border-radius: 50%;
                }
              }
            }
          }

          .profile-info {
            padding: 40px 20px 20px;
            text-align: center;

            .name {
              margin: 0 0 5px;
              font-size: 18px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }

            .position {
              margin: 0 0 20px;
              color: var(--el-text-color-regular);
              font-size: 14px;
            }

            .quick-stats {
              display: flex;
              justify-content: space-around;
              padding: 15px 0;
              border-top: 1px solid var(--el-border-color-light);

              .stat-item {
                text-align: center;

                .stat-number {
                  display: block;
                  font-size: 14px;
                  font-weight: 600;
                  color: var(--el-text-color-primary);
                  margin-bottom: 5px;
                }

                .stat-label {
                  font-size: 12px;
                  color: var(--el-text-color-regular);
                }
              }
            }
          }

          .outer-info {
            padding: 0 20px 20px;

            .info-item {
              display: flex;
              align-items: center;
              padding: 8px 0;
              color: var(--el-text-color-regular);

              i {
                margin-right: 10px;
                color: var(--el-color-primary);
                font-size: 16px;
              }

              span {
                font-size: 14px;
              }
            }
          }
        }

        .quick-nav {
          background: var(--el-bg-color);
          border-radius: 12px;
          padding: 20px;

          .nav-header {
            margin-bottom: 16px;

            h3 {
              margin: 0;
              font-size: 16px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }
          }

          .nav-items {
            display: flex;
            flex-direction: column;
            gap: 12px;

            .nav-item {
              display: flex;
              align-items: center;
              padding: 16px;
              background: var(--el-fill-color-light);
              border: 1px solid var(--el-border-color);
              border-radius: 10px;
              cursor: pointer;
              transition: all 0.3s ease;

              &:hover {
                border-color: var(--el-color-primary-light-5);
                background: var(--el-color-primary-light-9);
                transform: translateX(4px);
              }

              .nav-icon {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
                margin-right: 12px;

                i {
                  font-size: 18px;
                  color: #fff;
                }

                &.login-icon {
                  background: var(--el-color-primary);
                }

                &.operation-icon {
                  background: var(--el-color-warning);
                }

                &.notification-icon {
                  background: var(--el-color-info);
                }
              }

              .nav-content {
                flex: 1;

                h4 {
                  margin: 0 0 4px;
                  font-size: 14px;
                  font-weight: 600;
                  color: var(--el-text-color-primary);
                }

                p {
                  margin: 0;
                  font-size: 12px;
                  color: var(--el-text-color-regular);
                }
              }

              .arrow {
                font-size: 14px;
                color: var(--el-text-color-secondary);
                transition: transform 0.3s ease;
              }

              &:hover .arrow {
                transform: translateX(4px);
                color: var(--el-color-primary);
              }
            }
          }
        }
      }

      .right-wrap {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 20px;

        .info {
          padding: 20px;
          border-radius: 12px;
          background: var(--el-bg-color);

          .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--el-border-color-light);

            .title {
              display: flex;
              align-items: center;
              gap: 12px;
              margin: 0;
              font-size: 18px;
              font-weight: 600;
              color: var(--el-text-color-primary);

              i {
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                background: var(--el-color-primary);
                font-size: 18px;
                color: #fff;
                margin-right: 0;
              }
            }
          }

          .form {
            .form-grid {
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 20px;
              margin-bottom: 20px;

              .el-form-item {
                margin-bottom: 0;
              }
            }

            :deep(.el-input) {
              .el-input__wrapper {
                border-radius: 8px;
              }
            }

            :deep(.el-select) {
              .el-select__wrapper {
                border-radius: 8px;
              }
            }

            :deep(.el-textarea) {
              .el-textarea__inner {
                border-radius: 8px;
              }
            }
          }

          &.security-section {
            .security-items {
              display: flex;
              flex-direction: column;
              gap: 12px;

              .security-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px;
                background: var(--el-fill-color-light);
                border: 1px solid var(--el-border-color);
                border-radius: 10px;
                transition: all 0.3s ease;

                &:hover {
                  border-color: var(--el-color-primary-light-5);
                  background: var(--el-color-primary-light-9);
                }

                .security-info {
                  display: flex;
                  align-items: center;

                  .security-icon {
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 10px;
                    margin-right: 12px;

                    i {
                      font-size: 18px;
                      color: #fff;
                    }

                    &.password-icon {
                      background: var(--el-color-primary);
                    }

                    &.email-icon {
                      background: var(--el-color-success);
                    }

                    &.phone-icon {
                      background: var(--el-color-warning);
                    }
                  }

                  .security-content {
                    h3 {
                      margin: 0 0 4px;
                      font-size: 14px;
                      font-weight: 600;
                      color: var(--el-text-color-primary);
                    }

                    p {
                      margin: 0;
                      font-size: 12px;
                      color: var(--el-text-color-regular);
                    }
                  }
                }

                .el-button {
                  border-radius: 20px;
                }
              }
            }
          }
        }
      }
    }
  }

  // 对话框样式
  :deep(.el-dialog) {
    border-radius: 12px;
    overflow: hidden;

    .el-dialog__header {
      border-bottom: 1px solid var(--el-border-color-light);
      padding: 16px 20px;

      .el-dialog__title {
        font-size: 16px;
        font-weight: 600;
      }
    }

    .el-dialog__body {
      padding: 20px;
    }

    .el-dialog__footer {
      padding: 12px 20px;
      border-top: 1px solid var(--el-border-color-light);

      .el-button {
        border-radius: 8px;
      }
    }
  }

  @media only screen and (max-width: 1200px) {
    .page-content {
      .content {
        flex-direction: column;
        gap: 20px;

        .left-wrap {
          width: 100%;
        }

        .right-wrap {
          width: 100%;
        }
      }
    }
  }

  @media only screen and (max-width: 768px) {
    .page-content {
      .content {
        .info {
          .form {
            .form-grid {
              grid-template-columns: 1fr;
              gap: 16px;
            }
          }

          &.security-section {
            .security-items {
              .security-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 16px;

                .security-info {
                  width: 100%;
                }

                .el-button {
                  width: 100%;
                }
              }
            }
          }
        }
      }
    }
  }
</style>
