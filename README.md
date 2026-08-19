# 若依系统自动化测试项目

## 项目简介
基于若依管理系统的接口+UI自动化测试项目

## 技术栈
pytest + requests + playwright + allure

## 项目结构
- testcases/api：接口自动化用例
- testcases/ui：UI自动化用例
- pages：Page Object页面类
- data：测试数据（yaml）

## 运行方式
pip install -r requirements.txt
pytest（全部运行）
pytest testcases/api（只跑接口）
pytest testcases/ui（只跑UI）
allure serve ./allure-results（查看报告）