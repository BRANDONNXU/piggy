# -*- coding=utf-8
from qcloud_cos import CosConfig, CosServiceError, CosClientError
from qcloud_cos import CosS3Client
import sys
import os
import logging
from django_project import settings

secret_Id = settings.TENCENT_COS_ID  # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
secret_Key = settings.TENCENT_COS_KEY  # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140


def create_bucket(Bucket, region='ap-guangzhou'):
    # 正常情况日志级别使用 INFO，需要定位时可以修改为 DEBUG，此时 SDK 会打印和服务端的通信信息
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # 1. 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在 CosConfig 中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
    # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
    token = None  # 如果使用永久密钥不需要填入 token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见 https://cloud.tencent.com/document/product/436/14048
    scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
    config = CosConfig(Region=region, SecretId=secret_Id, SecretKey=secret_Key, Token=token, Scheme=scheme)
    client = CosS3Client(config)

    client.create_bucket(
        Bucket=Bucket,
    )
    response = client.put_bucket_cors(
        Bucket=Bucket,
        CORSConfiguration={
            'CORSRule': [
                {
                    'MaxAgeSeconds': 500,
                    'AllowedOrigin': [
                        '*',
                    ],
                    'AllowedMethod': [
                        'POST', 'GET', 'DELETE', 'PUT', 'HEAD'
                    ],
                    'AllowedHeader': [
                        '*',
                    ],
                    'ExposeHeader': [
                        '*',
                    ]
                }
            ]
        },
    )


# def upload_file():
#     response = client.upload_file(
#         Bucket='test-1320839699',
#         LocalFilePath='pizza.py',
#         Key='test.py',
#     )
#     print(response['ETag'])


def delete_bucket(bucket, region):
    config = CosConfig(Region=region, SecretId=secret_Id, SecretKey=secret_Key)
    client = CosS3Client(config)
    # 批量删除文件
    while True:
        part_object = client.list_objects(bucket)
        contents = part_object.get('Contents')
        if not contents:
            break
        objects = {
            "Quiet": "true",
            "Object": [{'Key': item['key']} for item in contents],
        }
        client.delete_objects(bucket, objects)
        if part_object['IsTruncated'] == 'false':
            break
    # 删除文件碎片
    while True:
        part_upload = client.list_multipart_uploads(bucket)
        uploads = part_upload.get('Upload')
        if not uploads:
            break
        for item in uploads:
            client.abort_multipart_upload(bucket, item['Key'], item['UploadId'])
        if part_upload['IsTruncated'] == 'false':
            break
    client.delete_bucket(bucket)


def delete_object(bucket, region, key):
    config = CosConfig(Region=region, SecretId=secret_Id, SecretKey=secret_Key)
    client = CosS3Client(config)

    response = client.delete_object(
        Bucket=bucket,
        Key=key
    )
    return response


def cos_download_file(bucket, region, key, file_path):
    secret_id = secret_Id  # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    secret_key = secret_Key  # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    region = region  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    response = client.get_object(
        Bucket=bucket,
        Key=key
    )
    return response['Body'].get_raw_stream()
