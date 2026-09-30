UPDATE sys_config
SET config_value = 'false'
WHERE config_key = 'sys.account.captchaEnabled';

UPDATE sys_user
SET nick_name = CONVERT(0xE88BA5E4BE9D USING utf8mb4)
WHERE user_name = 'admin';
