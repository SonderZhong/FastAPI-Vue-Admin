# _*_ coding : UTF-8 _*_
# @Time : 2025/01/03
# @Author : sonder
# @File : schema_tools.py
# @Comment : Schema生成工具

import re
from pathlib import Path
from typing import Dict, List, Any

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
SCHEMAS_DIR = BASE_DIR / "schemas"
MODELS_DIR = BASE_DIR / "models"

# Tortoise字段类型到Pydantic字段类型的映射
FIELD_TYPE_MAPPING = {
    "CharField": "str",
    "TextField": "str", 
    "IntField": "int",
    "SmallIntField": "int",
    "BigIntField": "int",
    "FloatField": "float",
    "DecimalField": "float",
    "BooleanField": "bool",
    "DateField": "str",  # 使用字符串表示日期
    "DatetimeField": "str",  # 使用字符串表示日期时间
    "TimeField": "str",  # 使用字符串表示时间
    "JSONField": "dict",
    "UUIDField": "str",
    "ForeignKeyField": "Optional[str]",  # 外键通常是可选的字符串ID
    "OneToOneField": "Optional[str]",
    "ManyToManyField": "List[str]"  # 多对多关系用字符串ID列表表示
}


def analyze_model_file(model_file_path: Path) -> List[Dict[str, Any]]:
    """分析模型文件，提取模型信息"""
    if not model_file_path.exists():
        return []
    
    content = model_file_path.read_text(encoding="utf-8")
    models = []
    
    # 查找所有模型类
    class_pattern = r'class\s+(\w+)\(BaseModel\):(.*?)(?=class\s+\w+|$)'
    class_matches = re.findall(class_pattern, content, re.DOTALL)
    
    for class_name, class_content in class_matches:
        # 提取类文档字符串 - 改进的正则表达式
        doc_match = re.search(r'"""(.*?)"""', class_content, re.DOTALL)
        if doc_match:
            # 清理文档字符串，移除多余的空白和换行
            description = doc_match.group(1).strip()
            # 只取第一行作为简短描述
            description = description.split('\n')[0].strip()
            if not description:
                description = f"{class_name}模型"
        else:
            description = f"{class_name}模型"
        
        # 提取字段信息
        fields = []
        field_pattern = r'(\w+)\s*=\s*fields\.(\w+)\((.*?)\)'
        field_matches = re.findall(field_pattern, class_content, re.DOTALL)
        
        for field_name, field_type, field_params in field_matches:
            field_info = parse_field_params(field_name, field_type, field_params)
            fields.append(field_info)
        
        models.append({
            "name": class_name,
            "description": description,
            "fields": fields,
            "file": model_file_path.name
        })
    
    return models


def parse_field_params(field_name: str, field_type: str, params_str: str) -> Dict[str, Any]:
    """解析字段参数"""
    field_info = {
        "name": field_name,
        "type": field_type,
        "pydantic_type": FIELD_TYPE_MAPPING.get(field_type, "str"),
        "required": True,
        "default": None,
        "description": "",
        "max_length": None,
        "null": False
    }
    
    # 解析参数
    if "null=True" in params_str:
        field_info["null"] = True
        field_info["required"] = False
    
    if "default=" in params_str:
        field_info["required"] = False
        # 提取默认值
        default_match = re.search(r'default=([^,\n)]+)', params_str)
        if default_match:
            field_info["default"] = default_match.group(1).strip()
    
    # 提取描述
    desc_match = re.search(r'description="([^"]*)"', params_str)
    if desc_match:
        field_info["description"] = desc_match.group(1)
    
    # 提取最大长度
    max_length_match = re.search(r'max_length=(\d+)', params_str)
    if max_length_match:
        field_info["max_length"] = int(max_length_match.group(1))
    
    # 处理外键字段
    if field_type in ["ForeignKeyField", "OneToOneField"]:
        field_info["pydantic_type"] = "Optional[str]"
        field_info["required"] = False
    
    # 如果字段可以为null，调整pydantic类型
    if field_info["null"] and field_info["pydantic_type"] != "Optional[str]":
        if not field_info["pydantic_type"].startswith("Optional"):
            field_info["pydantic_type"] = f"Optional[{field_info['pydantic_type']}]"
    
    return field_info


def generate_schema_code(model_info: Dict[str, Any], schema_types: List[str]) -> str:
    """生成schema代码"""
    model_name = model_info["name"]
    description = model_info["description"]
    fields = model_info["fields"]
    
    # 文件头部 - 简化描述，避免多行注释问题
    simple_description = description.split('\n')[0].strip() if description else f"{model_name}模型"
    
    code = f"""# _*_ coding : UTF-8 _*_
# @Time : {__import__('datetime').datetime.now().strftime('%Y/%m/%d %H:%M')}
# @Author : sonder
# @File : {model_name.lower().replace('system', '')}.py
# @Comment : {simple_description}

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from schemas.common import BaseResponse, ListQueryResult, DataBaseModel

"""
    
    # 生成不同类型的schema
    for schema_type in schema_types:
        if schema_type == "info":
            code += generate_info_schema(model_name, simple_description, fields)
        elif schema_type == "add":
            code += generate_add_schema(model_name, simple_description, fields)
        elif schema_type == "update":
            code += generate_update_schema(model_name, simple_description, fields)
        elif schema_type == "list":
            code += generate_list_schemas(model_name, simple_description)
        elif schema_type == "response":
            code += generate_response_schemas(model_name, simple_description)
    
    return code


def generate_info_schema(model_name: str, description: str, fields: List[Dict]) -> str:
    """生成信息模型schema"""
    class_name = f"{model_name.replace('System', '')}Info"
    
    code = f"""
class {class_name}(DataBaseModel):
    \"\"\"
    {description}信息模型
    \"\"\"
    model_config = ConfigDict()
"""
    
    for field in fields:
        field_name = field["name"]
        pydantic_type = field["pydantic_type"]
        description = field["description"]
        max_length = field["max_length"]
        default = field["default"]
        required = field["required"]
        
        # 构建Field参数
        field_params = []
        if not required:
            if default is not None:
                field_params.append(f"default={default}")
            else:
                field_params.append("default=None")
        else:
            field_params.append("...")
        
        if max_length:
            field_params.append(f"max_length={max_length}")
        
        if description:
            field_params.append(f'description="{description}"')
        
        field_def = f"Field({', '.join(field_params)})"
        
        code += f"    {field_name}: {pydantic_type} = {field_def}\n"
    
    code += "\n"
    return code


def generate_add_schema(model_name: str, description: str, fields: List[Dict]) -> str:
    """生成添加参数schema"""
    class_name = f"Add{model_name.replace('System', '')}Params"
    
    code = f"""
class {class_name}(BaseModel):
    \"\"\"
    添加{description}参数模型
    \"\"\"
    model_config = ConfigDict()
"""
    
    for field in fields:
        # 跳过自动生成的字段
        if field["name"] in ["id", "created_at", "updated_at", "is_del"]:
            continue
            
        field_name = field["name"]
        pydantic_type = field["pydantic_type"]
        description = field["description"]
        max_length = field["max_length"]
        default = field["default"]
        required = field["required"]
        
        # 对于添加操作，某些字段可能是必需的
        if field["name"] in ["password"] and field["null"]:
            required = True
            pydantic_type = pydantic_type.replace("Optional[", "").replace("]", "")
        
        # 构建Field参数
        field_params = []
        if not required:
            if default is not None:
                field_params.append(f"default={default}")
            else:
                field_params.append("default=None")
        else:
            field_params.append("...")
        
        if max_length:
            field_params.append(f"max_length={max_length}")
        
        if description:
            field_params.append(f'description="{description}"')
        
        field_def = f"Field({', '.join(field_params)})"
        
        code += f"    {field_name}: {pydantic_type} = {field_def}\n"
    
    code += "\n"
    return code


def generate_update_schema(model_name: str, description: str, fields: List[Dict]) -> str:
    """生成更新参数schema"""
    class_name = f"Update{model_name.replace('System', '')}Params"
    
    code = f"""
class {class_name}(BaseModel):
    \"\"\"
    更新{description}参数模型
    \"\"\"
    model_config = ConfigDict()
"""
    
    for field in fields:
        # 跳过自动生成的字段和ID字段
        if field["name"] in ["id", "created_at", "updated_at", "is_del"]:
            continue
            
        field_name = field["name"]
        pydantic_type = field["pydantic_type"]
        description = field["description"]
        max_length = field["max_length"]
        
        # 更新操作中所有字段都是可选的
        if not pydantic_type.startswith("Optional"):
            pydantic_type = f"Optional[{pydantic_type}]"
        
        # 构建Field参数
        field_params = ["default=None"]
        
        if max_length:
            field_params.append(f"max_length={max_length}")
        
        if description:
            field_params.append(f'description="{description}"')
        
        field_def = f"Field({', '.join(field_params)})"
        
        code += f"    {field_name}: {pydantic_type} = {field_def}\n"
    
    code += "\n"
    return code


def generate_list_schemas(model_name: str, description: str) -> str:
    """生成列表相关schema"""
    base_name = model_name.replace('System', '')
    
    code = f"""
class Get{base_name}ListResult(ListQueryResult):
    \"\"\"
    获取{description}列表结果模型
    \"\"\"
    result: List[{base_name}Info] = Field(default=[], description="{description}列表")

"""
    return code


def generate_response_schemas(model_name: str, description: str) -> str:
    """生成响应相关schema"""
    base_name = model_name.replace('System', '')
    
    code = f"""
class Get{base_name}InfoResponse(BaseResponse):
    \"\"\"
    获取{description}详情响应模型
    \"\"\"
    data: {base_name}Info = Field(default=None, description="{description}信息")


class Get{base_name}ListResponse(BaseResponse):
    \"\"\"
    获取{description}列表响应模型
    \"\"\"
    data: Get{base_name}ListResult = Field(default=None, description="响应数据")

"""
    return code


def create_schema_file(model_name: str, schema_types: List[str]) -> str:
    """创建schema文件"""
    try:
        # 查找对应的模型文件
        model_file = None
        for file_path in MODELS_DIR.glob("*.py"):
            if file_path.name in ["__init__.py", "common.py"]:
                continue
            
            content = file_path.read_text(encoding="utf-8")
            if f"class {model_name}(BaseModel):" in content:
                model_file = file_path
                break
        
        if not model_file:
            return f"未找到模型 {model_name}"
        
        # 检查schema文件是否已存在
        schema_filename = f"{model_name.lower().replace('system', '')}.py"
        schema_file = SCHEMAS_DIR / schema_filename
        
        if schema_file.exists():
            return f"⚠️ Schema文件 {schema_filename} 已存在，跳过生成以避免覆盖现有文件。如需强制覆盖，请使用 create_schema_from_model_force 工具"
        
        # 分析模型文件
        models = analyze_model_file(model_file)
        target_model = None
        
        for model in models:
            if model["name"] == model_name:
                target_model = model
                break
        
        if not target_model:
            return f"在文件 {model_file.name} 中未找到模型 {model_name}"
        
        # 生成schema代码
        schema_code = generate_schema_code(target_model, schema_types)
        
        # 确保schemas目录存在
        SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        schema_file.write_text(schema_code, encoding="utf-8")
        
        return f"✅ Schema文件 {schema_filename} 创建成功"
        
    except Exception as e:
        return f"创建schema文件失败: {str(e)}"


def list_available_models() -> str:
    """列出可用的模型"""
    try:
        models = []
        
        if not MODELS_DIR.exists():
            return "模型目录不存在"
        
        for file_path in MODELS_DIR.glob("*.py"):
            if file_path.name in ["__init__.py", "common.py"]:
                continue
            
            content = file_path.read_text(encoding="utf-8")
            
            # 提取模型类名
            class_matches = re.findall(r'class\s+(\w+)\(BaseModel\):', content)
            
            if class_matches:
                models.append({
                    "file": file_path.name,
                    "models": class_matches
                })
        
        if not models:
            return "未找到任何模型"
        
        result = "可用模型列表:\n"
        for model_info in models:
            result += f"\n📁 {model_info['file']}\n"
            for model_name in model_info['models']:
                result += f"   └── {model_name}\n"
        
        return result
        
    except Exception as e:
        return f"获取模型列表失败: {str(e)}"


def list_existing_schemas() -> str:
    """列出现有的schema文件"""
    try:
        if not SCHEMAS_DIR.exists():
            return "Schemas目录不存在"
        
        schema_files = []
        for file_path in SCHEMAS_DIR.glob("*.py"):
            if file_path.name == "__init__.py":
                continue
            schema_files.append(file_path.name)
        
        if not schema_files:
            return "未找到任何schema文件"
        
        result = "现有Schema文件:\n"
        for filename in sorted(schema_files):
            result += f"  • {filename}\n"
        
        return result
        
    except Exception as e:
        return f"获取schema列表失败: {str(e)}"


def create_schema_file_force(model_name: str, schema_types: List[str]) -> str:
    """强制创建schema文件（覆盖现有文件）"""
    try:
        # 查找对应的模型文件
        model_file = None
        for file_path in MODELS_DIR.glob("*.py"):
            if file_path.name in ["__init__.py", "common.py"]:
                continue
            
            content = file_path.read_text(encoding="utf-8")
            if f"class {model_name}(BaseModel):" in content:
                model_file = file_path
                break
        
        if not model_file:
            return f"未找到模型 {model_name}"
        
        # 分析模型文件
        models = analyze_model_file(model_file)
        target_model = None
        
        for model in models:
            if model["name"] == model_name:
                target_model = model
                break
        
        if not target_model:
            return f"在文件 {model_file.name} 中未找到模型 {model_name}"
        
        # 生成schema代码
        schema_code = generate_schema_code(target_model, schema_types)
        
        # 创建schema文件
        schema_filename = f"{model_name.lower().replace('system', '')}.py"
        schema_file = SCHEMAS_DIR / schema_filename
        
        # 确保schemas目录存在
        SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 写入文件（强制覆盖）
        schema_file.write_text(schema_code, encoding="utf-8")
        
        status = "覆盖" if schema_file.exists() else "创建"
        return f"✅ Schema文件 {schema_filename} {status}成功"
        
    except Exception as e:
        return f"创建schema文件失败: {str(e)}"
def register(mcp):
    """注册schema工具到 MCP 服务器"""
    
    @mcp.tool()
    def create_schema_from_model(
        model_name: str,
        schema_types: list = None
    ) -> str:
        """
        根据模型创建schema文件（不覆盖现有文件）
        
        Args:
            model_name: 模型类名（如：SystemUser）
            schema_types: 要生成的schema类型列表，可选值：["info", "add", "update", "list", "response"]
                        默认生成所有类型
        
        Returns:
            创建结果信息
        """
        if schema_types is None:
            schema_types = ["info", "add", "update", "list", "response"]
        
        return create_schema_file(model_name, schema_types)
    
    @mcp.tool()
    def create_schema_from_model_force(
        model_name: str,
        schema_types: list = None
    ) -> str:
        """
        根据模型强制创建schema文件（覆盖现有文件）
        
        Args:
            model_name: 模型类名（如：SystemUser）
            schema_types: 要生成的schema类型列表，可选值：["info", "add", "update", "list", "response"]
                        默认生成所有类型
        
        Returns:
            创建结果信息
        """
        if schema_types is None:
            schema_types = ["info", "add", "update", "list", "response"]
        
        return create_schema_file_force(model_name, schema_types)
    
    @mcp.tool()
    def list_available_models_for_schema() -> str:
        """
        列出可用于生成schema的模型
        
        Returns:
            可用模型列表
        """
        return list_available_models()
    
    @mcp.tool()
    def list_existing_schema_files() -> str:
        """
        列出现有的schema文件
        
        Returns:
            现有schema文件列表
        """
        return list_existing_schemas()
    
    @mcp.tool()
    def analyze_model_structure(model_name: str) -> str:
        """
        分析模型结构，显示字段信息
        
        Args:
            model_name: 模型类名
            
        Returns:
            模型结构分析结果
        """
        try:
            # 查找对应的模型文件
            model_file = None
            for file_path in MODELS_DIR.glob("*.py"):
                if file_path.name in ["__init__.py", "common.py"]:
                    continue
                
                content = file_path.read_text(encoding="utf-8")
                if f"class {model_name}(BaseModel):" in content:
                    model_file = file_path
                    break
            
            if not model_file:
                return f"未找到模型 {model_name}"
            
            # 分析模型文件
            models = analyze_model_file(model_file)
            target_model = None
            
            for model in models:
                if model["name"] == model_name:
                    target_model = model
                    break
            
            if not target_model:
                return f"在文件 {model_file.name} 中未找到模型 {model_name}"
            
            # 格式化输出
            result = f"模型分析: {model_name}\n"
            result += f"描述: {target_model['description']}\n"
            result += f"文件: {target_model['file']}\n\n"
            result += "字段列表:\n"
            
            for field in target_model['fields']:
                result += f"  • {field['name']}: {field['type']} -> {field['pydantic_type']}\n"
                if field['description']:
                    result += f"    描述: {field['description']}\n"
                if field['max_length']:
                    result += f"    最大长度: {field['max_length']}\n"
                result += f"    必需: {'是' if field['required'] else '否'}\n"
                if field['default'] is not None:
                    result += f"    默认值: {field['default']}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"分析模型结构失败: {str(e)}"