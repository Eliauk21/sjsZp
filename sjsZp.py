import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
# 调用浏览器
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
import json
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# 配置信息
LOGIN_URL = "https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fsjs-zx.jd.com"
INDEX_URL = "https://sjs-zx.jd.com/index.html"
TARGET_URL = "https://sjs-zx.jd.com/template/modularTemplate.html"
# 编辑模板页面
TEMPLATEID_URL = "https://sdk.jd.com/nm?tpGrade=3&templateId="# templateId 为模板号.tpGrade 为 1 是普通模块，3 时为定制模板
# 审核模板页面
TEMPLATEID_PREVIEW_URL = "https://sjs-zx.jd.com/template/applyAudit.html?templateId="# templateId 为模板号.tpGrade 为 1 是普通模块，3 时为定制模板

accessKeyId="DC2A7D48BBAF83143873C80869FDE38B"
accessKeySecret="02DB4A15CEDF23B8CE32E03EF06E0A73"

USERNAME = "陆泽科技"
PASSWORD = "bA6#aA1$pG2%"
root_dir = Path(__file__).resolve().parent
# root_dir='D:\\project\\ai-sms-review\\sjsZp\\'
# 是否为更新
isUpdate = False

operation = 'check_orderId'
# 'check_orderId' 店铺订购预审核   'generate_image'创建图片
# 'create_module'新建模版 'new_module'新建模块 'delete_fail_module' 失败模块重新打包  'edit_old_module' 打包高版本模块
# 'delete_module' 删除指定模块 'review_module' 提审模块

# 编辑模板
def edit_template(driver):
    # 读取 JSON 文件并循环
    with open(root_dir / "zipdist" /"shopConfig.json", "r", encoding='utf-8') as file:
        shopConfig = json.load(file)

    # 新建提审操作特殊处理：只需要调用一次，方法内部会遍历所有店铺
    if operation == "check_orderId":
        check_orderId(driver)
        return

    # 遍历 json 格式的 shopConfig
    for item in shopConfig:
            templateId = item["templateId"]

            if operation == "create_module":
                # create_module 不需要 templateId，直接导航到目标页面
                driver.get(TARGET_URL)
                create_module(driver, item)
            elif operation == "new_module":
                driver.get(TEMPLATEID_URL + templateId)
                new_module(driver, item["shopId"])
            elif operation == "delete_fail_module":
                driver.get(TEMPLATEID_URL + templateId)
                delete_fail_module(driver)
            elif operation == "edit_old_module":
                driver.get(TEMPLATEID_URL + templateId)
                edit_old_module(driver, item["shopId"])
            elif operation == "delete_module":
                driver.get(TEMPLATEID_URL + templateId)
                delete_module(driver, item["shopId"])
            elif operation == "review_module":
                driver.get(TEMPLATEID_URL + templateId)
                review_module(driver)

            else:
                print(f"未知的操作：{operation}")

def create_image(
    text: str = "Hello",
    bg_color: str = "#ffffff",
    text_color: str = "#000000",
    border_color: str = "#000000",
    width: int = 640,
    height: int = 914,
    border_width: int = 20,
    font_size: int = 48,
    font_path: Optional[str] = None,
    output_dir: str = ".",
    filename_prefix: Optional[str] = None,
) -> Path:
    """
    生成带围边的图片

    Args:
        text: 图片中心的文字
        bg_color: 背景颜色 (HEX 格式，如 #ffffff)
        text_color: 文字颜色 (HEX 格式)
        border_color: 围边颜色 (HEX 格式)
        width: 图片宽度 (包含围边)
        height: 图片高度 (包含围边)
        border_width: 围边宽度 (像素)
        font_size: 文字大小 (像素)
        font_path: 字体文件路径，默认使用系统字体
        output_dir: 输出目录

    Returns:
        生成图片的路径
    """
    # 计算内容区域 (去除围边)
    inner_width = width - 2 * border_width
    inner_height = height - 2 * border_width

    # 创建图片 (先画围边背景)
    img = Image.new("RGB", (width, height), border_color)

    # 绘制内部背景
    draw = ImageDraw.Draw(img)
    inner_rect = [
        border_width,
        border_width,
        width - border_width,
        height - border_width,
    ]
    draw.rectangle(inner_rect, fill=bg_color)

    # 加载字体
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        # 尝试加载中文字体
        system_fonts = [
            "C:/Windows/Fonts/simhei.ttf",      # 黑体
            "C:/Windows/Fonts/simsun.ttc",      # 宋体
            "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
            "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        font = ImageFont.load_default()
        for font_file in system_fonts:
            try:
                font = ImageFont.truetype(font_file, font_size)
                break
            except Exception:
                continue

    # 计算文字位置 (居中)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (inner_width - text_width) // 2 + border_width
    text_y = (inner_height - text_height) // 2 + border_width

    # 绘制文字
    draw.text((text_x, text_y), text, fill=text_color, font=font)

    # 生成文件名
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 创建文件名
    prefix = filename_prefix if filename_prefix else "".join(c if c.isalnum() or c in "-_." else "_" for c in text[:20])
    filename = f"{prefix}.png"
    filepath = output_path / filename

    # 保存图片
    img.save(filepath, "PNG")
    print(f"  已生成：{filepath}")

    return filepath


def generate_batch(
    config_path: str = "shopConfig.json",
    output_subdir: str = "image",
    bg_color: str = "#ffffff",
    text_color: str = "#000000",
    border_color: str = "#000000",
    border_width: int = 20,
    font_size: int = 40,
) -> list:
    """
    批量生成图片

    Args:
        config_path: shopConfig.json 文件路径
        output_subdir: 输出子目录名 (默认：image)
        bg_color: 背景颜色
        text_color: 文字颜色
        border_color: 围边颜色
        border_width: 围边宽度
        font_size: 文字大小

    Returns:
        生成的图片路径列表
    """
    # 读取配置文件
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"配置文件不存在：{config_file}")
        return []

    with open(config_file, "r", encoding="utf-8") as f:
        shop_config = json.load(f)

    # 创建输出目录 (同级目录下的 image 文件夹)
    output_dir = config_file.parent / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"开始生成 {len(shop_config)} 张图片...")
    print(f"输出目录：{output_dir}")
    print(f"尺寸：640 x 914")
    print("-" * 50)

    generated_files = []

    for item in shop_config:
        shop_id = item.get("shopId", "unknown")
        shop_name = item.get("shopName", "Unknown")
        try:
            filepath = create_image(
                text=shop_name,
                bg_color=bg_color,
                text_color=text_color,
                border_color=border_color,
                width=640,
                height=914,
                border_width=border_width,
                font_size=font_size,
                output_dir=str(output_dir),
                filename_prefix=shop_id,
            )
            generated_files.append(filepath)
        except Exception as e:
            print(f"  生成失败 [{shop_name}]: {e}")

    print("-" * 50)
    print(f"完成！共生成 {len(generated_files)}/{len(shop_config)} 张图片")

    return generated_files

# 创建模版（为每个店铺配置定制模板）
def create_module(driver, shop_item):
    shop_name = shop_item["shopName"]

    try:
        # 1. 点击 btn-green-link 按钮
        edit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-green-link"))
        )
        edit_button.click()
        time.sleep(1)  # 等待弹窗出现

        # 2. 输入 shopName 到 tp-name J_tpName（先输入名称）
        tp_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tp-name"))
        )
        tp_name_input.clear()
        tp_name_input.send_keys(shop_name)
        time.sleep(0.5)

        # 3. 在弹窗中选择 value=3 的 option（tp-price J_tpType）
        tp_type_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tp-price"))
        )
        select_element = tp_type_select.find_element(By.TAG_NAME, "select")
        # 使用 Select 类处理下拉框
        select = Select(select_element)
        select.select_by_value("3")
        time.sleep(0.5)

        # 4. 点击 btn-yellow J-sure 按钮
        sure_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-yellow"))
        )
        sure_button.click()

        # 等待 2 秒后页面会自动跳转到新页面
        time.sleep(2)

        # 获取当前 URL 并提取 templateId
        current_url = driver.current_url
        print(f"当前页面 URL: {current_url}")

        # 从 URL 中提取 templateId (例如：https://sdk.jd.com/nm?tpGrade=3&templateId=31261)
        if "templateId=" in current_url:
            # 使用 parse_qs 解析 URL 参数
            from urllib.parse import parse_qs, urlparse
            parsed_url = urlparse(current_url)
            params = parse_qs(parsed_url.query)
            template_id = params.get("templateId", [None])[0]

            if template_id:
                print(f"提取到 templateId: {template_id}")
                # 更新传入的 shop_item 的 templateId
                shop_item["templateId"] = template_id

                # 读取完整配置文件，更新后写回
                with open(root_dir / "zipdist" / "shopConfig.json", "r", encoding='utf-8') as f:
                    shop_config = json.load(f)
                for config_item in shop_config:
                    if config_item["shopName"] == shop_name:
                        config_item["templateId"] = template_id
                        break
                with open(root_dir / "zipdist" / "shopConfig.json", "w", encoding='utf-8') as f:
                    json.dump(shop_config, f, ensure_ascii=False, indent=2)
                print(f"已更新店铺 {shop_name} 的 templateId 到 shopConfig.json")
            else:
                print(f"未能在 URL 中找到 templateId 参数 - 店铺：{shop_name}")
        else:
            print(f"URL 中不包含 templateId 参数 - 店铺：{shop_name}, URL: {current_url}")

        print(f"已完成店铺配置：{shop_name}")

        # 返回目标页面，继续下一个店铺的配置
        print("返回目标页面...")
        driver.get(TARGET_URL)
        time.sleep(2)  # 等待页面加载完成

    except TimeoutException as e:
        print(f"操作超时 - 店铺：{shop_name}, 错误：{str(e)}")
        # 尝试返回目标页面继续下一个
        driver.get(TARGET_URL)
        time.sleep(2)
    except Exception as e:
        print(f"创建模块失败 - 店铺：{shop_name}, 错误：{str(e)}")
        # 尝试返回目标页面继续下一个
        driver.get(TARGET_URL)
        time.sleep(2)


# 订单预审
def check_orderId(driver):
    """
    提审流程：
    1. 导航到订单管理页面，输入 shopId 搜索
    2. 获取表格第一行第一列的模板 ID
    3. 点击创建按钮，填写模板信息
    4. 导航到模板编辑页面提交审核
    """
    try:
        # 读取 shopConfig.json 获取所有店铺（只在开始时读取一次）
        shop_config_path = root_dir / "zipdist" / "shopConfig.json"
        with open(shop_config_path, "r", encoding='utf-8') as file:
            shop_config = json.load(file)

        # 订单管理页面 URL
        order_management_url = "https://sjs-zx.jd.com/rnTemplate/order-management.html"

        # 标记是否有更新
        has_update = False

        for shop_item in shop_config:
            # # 如果已经有 templateId，则跳过
            # if shop_item.get("templateId"):
            #     print(f"\n=== 店铺 {shop_item['shopName']} 已有模板 ID: {shop_item['templateId']}，跳过 ===")
            #     continue

            shop_id = shop_item["shopId"]
            shop_name = shop_item["shopName"]
            print(f"\n=== 开始处理店铺：{shop_name} ({shop_id}) ===")

            try:
                # 1. 导航到订单管理页面
                driver.get(order_management_url)
                time.sleep(2)

                # 2. 输入 shopId - 修复 XPath：先找到包含"店铺 ID"文本的父元素，再查找其下的 input
                shop_id_label = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '店铺ID：')]"))
                )
                shop_id_input = shop_id_label.find_element(By.XPATH, ".//following-sibling::input[@type='number'] | .//input[@type='number'] | .//following-sibling::*//input[@type='number']")
                shop_id_input.clear()
                shop_id_input.send_keys(shop_id)
                print(f"已输入 shopId: {shop_id}")
                time.sleep(0.5)

                # 3. 点击搜索按钮 - 先找到"搜索"span，再点击其父级 button
                time.sleep(1)
                search_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ant-btn"))
                )
                search_btn.click()
                print("已点击搜索按钮")
                time.sleep(2)

                # 4. 等待表格出现，并获取 tbody 中第一个 tr 的第一个 td 的内容
                try:
                    # 等待 tbody 出现，最多等待 10 秒
                    tbody = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ant-table-body tbody.ant-table-tbody"))
                    )
                    print("表格已加载")

                    # 获取 tbody 中第一个 tr
                    first_tr = tbody.find_element(By.CSS_SELECTOR, "tr.ant-table-row-level-0")

                    # 获取第一个 tr 中第一个 td 的内容
                    first_td = first_tr.find_element(By.CSS_SELECTOR, "td:first-child")
                    orderId = first_td.text.strip()

                    print(f"从表格中获取到订单 ID: {orderId}")

                    # 更新 shop_item 的 templateId
                    shop_item["orderId"] = orderId
                    has_update = True
                    print(f"已更新店铺 {shop_name} 的 orderId (内存中)")

                except TimeoutException:
                    # 没有表格出现，说明该店铺没有模板记录
                    print(f"警告：店铺 {shop_name} 搜索后未出现表格，可能没有模板记录")
                    continue
                except Exception as e:
                    print(f"店铺 {shop_name} 获取表格数据失败：{e}")
                    continue

            except Exception as e:
                print(f"店铺 {shop_name} 处理失败：{e}")
                import traceback
                traceback.print_exc()
                # 继续处理下一个店铺
                continue

        # 所有店铺处理完成后，一次性写入 shopConfig.json
        if has_update:
            with open(shop_config_path, "w", encoding='utf-8') as f:
                json.dump(shop_config, f, ensure_ascii=False, indent=2)
            print("\n=== 已保存更新到 shopConfig.json ===")

        print("\n=== 所有店铺提审完成 ===")

    except Exception as e:
        print(f"审核模块失败：{str(e)}")
        import traceback
        traceback.print_exc()

# 提交审核
def review_module(driver):
    try:
        edit_button = driver.find_element(By.CLASS_NAME, "J_save")
        if edit_button:
            edit_button.click()

            # 等待新窗口打开（假设点击后弹出新窗口）
            WebDriverWait(driver, 10).until(EC.new_window_is_opened)

            # 添加 5 秒的等待时间
            time.sleep(1)  # 在提交前等待 1 秒

            # 等待提交按钮出现并点击
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "J_submit"))
            )
            submit_button.click()
            time.sleep(5)

    except Exception as e:
        print(f"审核模块失败：{str(e)}")

# 删除模版
def delete_module(driver, shopId):
    try:
        time.sleep(1)

        li_elements = driver.find_elements(By.TAG_NAME, "li")

        # print(f"找到 {len(li_elements)} 个 li 元素")

        for li_element in li_elements:
            # 使用 find_elements 避免抛出异常
            status_spans = li_element.find_elements(By.XPATH, ".//span[@class='cd-item-name' and @title='阶梯礼']")

            if status_spans:
                delete_btns = li_element.find_elements(By.XPATH, ".//div[contains(@class, 'J_delete')]")

                if delete_btns:
                    time.sleep(0.5)
                    delete_btns[0].click()
                    # print("成功点击删除按钮")

                    # 等待弹窗出现并点击确认
                    try:
                        time.sleep(1)
                        confirm_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[@class='cd-btn-ok J_btnOK']"))
                        )
                        confirm_btn.click()
                        # print("已点击确认按钮")
                        time.sleep(1)

                        # 监控是否出现错误提示
                        try:
                            error_span = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.XPATH,
                                                                "//span[@class='cd-text J_text' and contains(text(), '为避续模块后续无法维护')]"))
                            )
                            if error_span:
                                print(f"使用中的模块不允许删除：{shopId}")
                        except TimeoutException:
                            # 未出现错误提示，属于正常情况
                            pass

                        time.sleep(1)
                    except TimeoutException:
                        print(f"自动化过程出错：{shopId}")
                # break  # 找到并处理完成后退出循环

    except Exception as e:
        print(f"自动化过程出错 final: {shopId}")

# 打包失败删除并重新创建
def delete_fail_module(driver):
    try:
        # 等待页面加载完成（等待模块列表出现）
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "li"))
            )
        except TimeoutException:
            print("等待模块列表加载超时")

        time.sleep(1)  # 额外等待，确保页面完全渲染

        # 从当前 URL 获取 templateId，然后从 shopConfig.json 中获取 shopId
        current_url = driver.current_url
        template_id = None
        if "templateId=" in current_url:
            from urllib.parse import parse_qs, urlparse
            parsed_url = urlparse(current_url)
            params = parse_qs(parsed_url.query)
            template_id = params.get("templateId", [None])[0]

        # 从 shopConfig.json 中获取 shopId
        shop_id = None
        if template_id:
            with open(root_dir / "zipdist" / "shopConfig.json", "r", encoding='utf-8') as f:
                shop_config = json.load(f)
            for config_item in shop_config:
                if config_item.get("templateId") == template_id:
                    shop_id = config_item.get("shopId")
                    break

        if not shop_id:
            print(f"未能获取 shopId，当前 URL: {current_url}, templateId: {template_id}")
            return

        print(f"当前模板 shopId: {shop_id}, templateId: {template_id}")

        # 读取 moduleConfig.json 获取模块配置
        with open(root_dir / "moduleConfig.json", "r", encoding='utf-8') as f:
            module_config = json.load(f)

        # 创建模块名称到配置的映射
        module_config_map = {item["name"]: item for item in module_config}

        # 使用其他方法查找状态为"打包失败"的模块
        # 1. 先找到所有 li 元素
        li_elements = driver.find_elements(By.TAG_NAME, "li")

        print(f"找到 {len(li_elements)} 个 li 元素")
        fail_count = 0
        recreate_count = 0

        for li_element in li_elements:
            # 2. 使用 find_elements (复数) 避免抛出异常，找不到时返回空列表
            status_spans = li_element.find_elements(By.XPATH, ".//span[@class='cd-item-status' and @data-type='4']")

            if not status_spans:
                # 当前模块不是"打包失败"状态，跳过
                continue

            # 获取模块名称
            module_name_span = li_element.find_elements(By.CLASS_NAME, "cd-item-name")
            module_name = module_name_span[0].get_attribute("title") if module_name_span else "未知模块"
            print(f"发现打包失败的模块：{module_name}")

            try:
                # 3. 找到删除按钮并点击
                delete_btns = li_element.find_elements(By.XPATH, ".//div[contains(@class, 'J_delete')]")

                if not delete_btns:
                    print("未找到删除按钮，跳过")
                    continue

                # 滚动到元素位置
                driver.execute_script("arguments[0].scrollIntoView();", delete_btns[0])
                time.sleep(0.5)

                # 点击删除按钮
                delete_btns[0].click()
                print(f"已点击删除按钮，模块：{module_name}")
                fail_count += 1

                # 4. 等待弹窗出现并点击确认
                try:
                    # 等待弹窗出现
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "cd-modal"))
                    )

                    # 点击确认按钮
                    confirm_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[@class='cd-btn-ok J_btnOK']"))
                    )
                    confirm_btn.click()
                    print("已点击确认按钮")
                    time.sleep(1)

                    # 5. 删除成功后，重新创建该模块
                    if module_name in module_config_map:
                        print(f"开始重新创建模块：{module_name}")
                        recreate_module(driver, shop_id, module_config_map[module_name])
                        recreate_count += 1
                    else:
                        print(f"未在 moduleConfig.json 中找到模块配置：{module_name}")

                except TimeoutException:
                    print("弹窗未出现或超时")

            except Exception as e:
                print(f"删除打包失败模块时出错：{e}")

        print(f"共删除 {fail_count} 个打包失败的模块，重新创建 {recreate_count} 个")

    except Exception as e:
        print(f"自动化过程出错：{e}")

# 重新创建模块
def recreate_module(driver, shop_id, module_item):
    """根据模块配置重新创建模块"""
    try:
        # 等待遮罩层消失
        try:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "cd-modal-overlay"))
            )
        except TimeoutException:
            print("遮罩层未消失，尝试强制点击")

        # 点击"添加模块"按钮
        add_module_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-green-link"))
        )
        try:
            add_module_button.click()
        except Exception as e:
            print("点击被拦截，尝试 JS 点击")
            driver.execute_script("arguments[0].click();", add_module_button)

        time.sleep(1)

        # 填写模块名称
        driver.find_element(By.ID, "moduleName").send_keys(module_item["name"])
        driver.find_element(By.ID, "moduleDesc").send_keys("  ")
        driver.find_element(By.ID, "accessKeyId").send_keys(accessKeyId)
        driver.find_element(By.ID, "accessKeySecret").send_keys(accessKeySecret)

        # 上传文件
        dynamic_path = root_dir / "zipdist" / shop_id / module_item["fileName"]
        dynamic_path_str = str(dynamic_path)
        driver.find_element(By.ID, "fileUpload").send_keys(dynamic_path_str)

        # 设置图片
        driver.execute_script(f"""
            var div = document.querySelector('.J_imagePanel');
            var imgUrl = '{module_item["img"]}';
            div.setAttribute('data-url', imgUrl);
            div.style.backgroundImage = 'url(' + imgUrl + ')';
        """)

        # 选择模块类型（会员卡/非会员卡）
        module_select = driver.find_element(By.CLASS_NAME, "cd-select-el")
        module_select.click()
        is_member_card = 4 if module_item.get("isMemberCard", False) else 5
        target_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@class='sim-list']//li[@str='{is_member_card}']"))
        )
        target_option.click()

        # 选择 Taro 版本
        time.sleep(1)
        all_selects = driver.find_elements(By.XPATH, "//div[contains(@class, 'cd-module-type-select')]")

        taro_version_dropdown = None
        for s in all_selects:
            text = s.text
            if "新版" in text or "v4" in text or "v3" in text:
                taro_version_dropdown = s.find_element(By.CLASS_NAME, "cd-select-el")
                break

        if not taro_version_dropdown:
            taro_version_dropdown = all_selects[1].find_element(By.CLASS_NAME, "cd-select-el")

        driver.execute_script("arguments[0].scrollIntoView(true);", taro_version_dropdown)
        time.sleep(0.5)
        taro_version_dropdown.click()
        time.sleep(0.5)

        # 选择 3.5.4 版本
        target_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'sim-list')]//li[contains(@str, '3.5.4')]"))
        )
        target_option.click()

        # 点击确认按钮
        driver.find_element(By.CLASS_NAME, "J_btnOK").click()
        time.sleep(2)

        print(f"成功重新创建模块：{module_item['name']}")

    except Exception as e:
        print(f"重新创建模块失败 - {module_item['name']}: {e}")

# 打包模块v3版本
def new_module(driver,shopId):
    # 获取要添加的模块
    with open("moduleConfig.json", "r", encoding='utf-8') as file:
        moduleConfig = json.load(file)
        for item in moduleConfig:
            try:
                # 等待遮罩层消失
                try:
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located((By.CLASS_NAME, "cd-modal-overlay"))
                    )
                except TimeoutException:
                    print("遮罩层未消失，尝试强制点击")

                # 定位并点击按钮（优先使用显式等待）
                add_module_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "J_addModule"))
                )
                # 尝试正常点击
                try:
                    add_module_button.click()
                except Exception as e:
                    print("点击被拦截，尝试 JS 点击")
                    driver.execute_script("arguments[0].click();", add_module_button)

                # driver.find_element(By.CLASS_NAME, "J_addModule").click()
                # id moduleName 填写模块名称
                driver.find_element(By.ID, "moduleName").send_keys(item["name"])
                driver.find_element(By.ID, "moduleDesc").send_keys("  ")
                driver.find_element(By.ID, "accessKeyId").send_keys(accessKeyId)
                driver.find_element(By.ID, "accessKeySecret").send_keys(accessKeySecret)
                # 确保 shopId 是字符串
                dynamic_path = root_dir / "zipdist" / shopId / item["fileName"]

                # 将 Path 对象转换为字符串（如果需要）
                dynamic_path_str = str(dynamic_path)
                #     获取程序根目录
                driver.find_element(By.ID, "fileUpload").send_keys(dynamic_path_str)

                driver.execute_script(f"""
                                var div = document.querySelector('.J_imagePanel');
                                var imgUrl = '{item["img"]}';
                                div.setAttribute('data-url', imgUrl);
                                div.style.backgroundImage = 'url(' + imgUrl + ')';
                            """)

                # 选模块
                module_select = driver.find_element(By.CLASS_NAME, "cd-select-el")
                module_select.click()
                isMemberCard=5
                if item["isMemberCard"]:
                    isMemberCard=4
                target_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[@class='sim-list']//li[@str='{isMemberCard}']"))
                )
                target_option.click()

                # 选版本 - 点击版本选择框
                time.sleep(1)  # 等待上一个选择完全关闭

                # 查找包含"新版"或"v4"文本的 cd-module-type-select 元素（即 Taro 版本选择器）
                all_selects = driver.find_elements(By.XPATH, "//div[contains(@class, 'cd-module-type-select')]")

                taro_version_dropdown = None
                for s in all_selects:
                    text = s.text
                    if "新版" in text or "v4" in text or "v3" in text:
                        taro_version_dropdown = s.find_element(By.CLASS_NAME, "cd-select-el")
                        break

                if not taro_version_dropdown:
                    # 备选方案：直接取第二个
                    taro_version_dropdown = all_selects[1].find_element(By.CLASS_NAME, "cd-select-el")

                driver.execute_script("arguments[0].scrollIntoView(true);", taro_version_dropdown)
                time.sleep(0.5)
                taro_version_dropdown.click()
                time.sleep(0.5)
                # 选择 3.5.4 版本
                target_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'sim-list')]//li[contains(@str, '3.5.4')]"))
                )
                target_option.click()

                driver.find_element(By.CLASS_NAME, "J_btnOK").click()

                time.sleep(2)
                print(f"成功创建模块：{item['name']}")
            except Exception as e:
                print(f"创建模块失败 - 模块：{item['name']}, 错误：{str(e)}")
                import traceback
                traceback.print_exc()

# 打包模块v4版本（还可以进行换图，换文件）
def edit_old_module(driver, shopId):
    # 等待页面加载完成（等待模块列表出现）
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "J_addModule"))
        )
    except TimeoutException:
        print(f"店铺{shopId}: 等待模块列表加载超时")
        return

    time.sleep(1)  # 额外等待，确保页面完全渲染

    # 读取 JSON 文件并循环
    with open(root_dir / "moduleConfig.json", "r", encoding='utf-8') as file:
        moduleConfig = json.load(file)

        for item in moduleConfig:
            try:
                # 等待遮罩层消失
                try:
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.CLASS_NAME, "cd-modal-overlay"))
                    )
                except TimeoutException:
                    pass  # 遮罩层可能不存在，继续

                name = item['name']
                print(f"店铺{shopId}: 正在编辑模块 - {name}")

                # 构建 XPath 表达式
                if "会员卡" in name:
                    xpath_expr = "//div[contains(@data-modulename, '会员卡')]"
                elif "橱窗" in name:
                    xpath_expr = "//div[contains(@data-modulename, '橱窗')]"
                elif "轮播" in name:
                    # 区分"轮播图"和"轮播弹窗"
                    xpath_expr = f"//div[contains(@data-modulename, '轮播图')]"
                elif "热区" in name:
                    xpath_expr = "//div[contains(@data-modulename, '热区')]"
                elif "积分" in name:
                    xpath_expr = "//div[contains(@data-modulename, '积分')]"
                elif "红包" in name:
                    xpath_expr = "//div[contains(@data-modulename, '红包')]"
                elif "弹窗" in name:
                    xpath_expr = "//div[contains(@data-modulename, '弹窗')]"
                elif "阶梯" in name:
                    xpath_expr = "//div[contains(@data-modulename, '阶梯')]"
                elif "促销" in name:
                    xpath_expr = "//div[contains(@data-modulename, '促销')]"
                else:
                    xpath_expr = f"//div[@data-modulename='{name}']"

                # 查找模块元素
                module_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath_expr))
                )

                if not module_element:
                    print(f"店铺{shopId}: 未找到模块 - {name}")
                    continue

                # 点击编辑按钮
                try:
                    edit_btn = module_element.find_element(By.CLASS_NAME, "J_edit")
                    driver.execute_script("arguments[0].click();", edit_btn)
                except Exception as e:
                    print(f"店铺{shopId}: 点击编辑按钮失败 - {name}, 错误：{e}")
                    continue

                time.sleep(0.5)

                # 填写 AK/SK
                try:
                    driver.find_element(By.ID, "accessKeyId").send_keys(accessKeyId)
                    driver.find_element(By.ID, "accessKeySecret").send_keys(accessKeySecret)
                except Exception as e:
                    print(f"店铺{shopId}: 填写 AK/SK 失败 - {name}, 错误：{e}")

                # 点击确认按钮
                try:
                    confirm_btn = driver.find_element(By.CLASS_NAME, "J_btnOK")
                    driver.execute_script("arguments[0].click();", confirm_btn)
                except Exception as e:
                    print(f"店铺{shopId}: 点击确认按钮失败 - {name}, 错误：{e}")
                    continue

                time.sleep(2)
                print(f"店铺{shopId}: 模块编辑成功 - {name}")

            except Exception as e:
                print(f"店铺{shopId}: 模块加载失败 - {item['name']}, 错误：{e}")

def main():
    if operation == "generate_image":
        # 批量生成模式（默认）
        generate_batch(
            config_path=root_dir / "zipdist" / "shopConfig.json",
            output_subdir="image",
            bg_color="#ffffff",
            text_color="#000000",
            border_color="#000000",
            border_width=20,
            font_size=40,
        )
    else:
        # service = Service(service_args=["--verbose"])
        # edge_options = Options()
        # edge_options.add_argument("--test-type")  # 禁用沙盒模式
        # edge_options.add_argument("--disable-popup-blocking")  # 禁用弹窗阻止
        # edge_options.add_argument("--disable-dev-shm-usage")
        options = Options()
        options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        # 使用独立的浏览器配置文件，允许同时运行多个浏览器实例
        options.add_argument(f"--user-data-dir={root_dir / 'edge_profile'}")
        driver_path = str(root_dir / "msedgedriver.exe")
        service = Service(executable_path=driver_path)
        driver = webdriver.Edge(service=service, options=options)

        try:
            driver.get(LOGIN_URL)
            # 登录，若 60 秒内登录成功则进行逻辑跳转
            wait = WebDriverWait(driver, 60)
            username_field = driver.find_element(By.ID, "loginname")
            password_field = driver.find_element(By.ID, "nloginpwd")
            username_field.send_keys(USERNAME)
            password_field.send_keys(PASSWORD)
            driver.find_element(By.ID, "loginsubmit").click()
            # 操作登录后需手动滑动验证码
            try:
                wait.until(EC.url_contains(INDEX_URL))
                print("登录成功")
            except TimeoutException:
                raise Exception("登录失败或超时")

            # 导航到目标页面
            driver.get(TARGET_URL)
            edit_template(driver)

        except Exception as e:
            print(f"操作失败：{str(e)}")
        finally:
            # 关闭浏览器
            input("按任意键退出...")
            driver.quit()

if __name__ == "__main__":
    main()
