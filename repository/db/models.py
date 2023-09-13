# coding: utf-8
# !/usr/bin/env python

""" models.py: Easy UCS Deployment Tool """

from sqlalchemy import Boolean, Column, Integer, JSON, LargeBinary, String
from sqlalchemy.types import DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BackupRecord(Base):
    __tablename__ = "backups"

    backup_file_extension = Column(String(4))
    backup_type = Column(String(16))
    device_name = Column(String(100))
    device_uuid = Column(String(36))
    device_version = Column(String(100))
    easyucs_version = Column(String(100))
    file_path = Column(String(256))
    file_type = Column(String(16))
    hash = Column(String(64))
    is_hidden = Column(Boolean())
    is_system = Column(Boolean())
    name = Column(String(256))
    origin = Column(String(16))
    system_usage = Column(String(100))
    timestamp = Column(DateTime())
    uuid = Column(String(36), nullable=False, primary_key=True)


class ConfigRecord(Base):
    __tablename__ = "configs"

    device_name = Column(String(100))
    device_uuid = Column(String(36))
    device_version = Column(String(100))
    easyucs_version = Column(String(100))
    file_path = Column(String(256))
    file_type = Column(String(16))
    hash = Column(String(64))
    is_hidden = Column(Boolean())
    is_system = Column(Boolean())
    name = Column(String(256))
    origin = Column(String(16))
    system_usage = Column(String(100))
    timestamp = Column(DateTime())
    uuid = Column(String(36), nullable=False, primary_key=True)

    category = Column(String(100))
    revision = Column(String(100))
    source_config_uuid = Column(String(36))
    source_device_uuid = Column(String(36))
    source_inventory_uuid = Column(String(36))
    subcategory = Column(String(100))
    url = Column(String(256))


class DeviceRecord(Base):
    __tablename__ = "devices"

    backups_path = Column(String(256))
    cached_orgs = Column(JSON)
    cache_path = Column(String(256))
    device_connector_claim_status = Column(String(16))
    device_connector_ownership_name = Column(String(256))
    device_connector_ownership_user = Column(String(256))
    device_name = Column(String(100))
    device_uuid = Column(String(36))
    device_version = Column(String(100))
    easyucs_version = Column(String(100))
    file_path = Column(String(256))
    file_type = Column(String(16))
    hash = Column(String(64))
    images_path = Column(String(256))
    intersight_device_uuid = Column(String(36))
    is_hidden = Column(Boolean())
    is_reachable = Column(Boolean())
    is_system = Column(Boolean())
    name = Column(String(256))
    origin = Column(String(16))
    system_usage = Column(String(100))
    timestamp = Column(DateTime())
    timestamp_last_connected = Column(DateTime())
    uuid = Column(String(36), nullable=False, primary_key=True)

    bypass_version_checks = Column(Boolean())
    device_type = Column(String(100))
    device_type_long = Column(String(100))
    key_id = Column(String(100))
    password = Column(LargeBinary)
    private_key_path = Column(String(256))
    target = Column(String(100))
    username = Column(String(100))


class InventoryRecord(Base):
    __tablename__ = "inventories"

    device_name = Column(String(100))
    device_uuid = Column(String(36))
    device_version = Column(String(100))
    easyucs_version = Column(String(100))
    file_path = Column(String(256))
    file_type = Column(String(16))
    hash = Column(String(64))
    is_hidden = Column(Boolean())
    is_system = Column(Boolean())
    name = Column(String(256))
    origin = Column(String(16))
    system_usage = Column(String(100))
    timestamp = Column(DateTime())
    uuid = Column(String(36), nullable=False, primary_key=True)


class ReportRecord(Base):
    __tablename__ = "reports"

    device_name = Column(String(100))
    device_uuid = Column(String(36))
    device_version = Column(String(100))
    easyucs_version = Column(String(100))
    file_path = Column(String(256))
    file_type = Column(String(16))
    hash = Column(String(64))
    is_hidden = Column(Boolean())
    is_system = Column(Boolean())
    name = Column(String(256))
    origin = Column(String(16))
    system_usage = Column(String(100))
    timestamp = Column(DateTime())
    uuid = Column(String(36), nullable=False, primary_key=True)

    config_uuid = Column(String(36))
    inventory_uuid = Column(String(36))
    language = Column(String(100))
    output_format = Column(String(100))
    page_layout = Column(String(100))
    report_type = Column(String(100))
    size = Column(String(100))
    target_device_uuid = Column(String(36))


class TagRecord(Base):
    __tablename__ = "tags"

    key = Column(String(100))
    value = Column(String(100))
    parent_uuid = Column(String(36), nullable=False)
    uuid = Column(String(36), nullable=False, primary_key=True)


class TaskRecord(Base):
    __tablename__ = "tasks"

    description = Column(String(256))
    easyucs_version = Column(String(100))
    name = Column(String(256))
    status = Column(String(16))
    status_message = Column(String(256))
    timestamp_start = Column(DateTime())
    timestamp_stop = Column(DateTime())
    uuid = Column(String(36), nullable=False, primary_key=True)

    config_uuid = Column(String(36))
    device_name = Column(String(100))
    device_uuid = Column(String(36))
    inventory_uuid = Column(String(36))
    report_uuid = Column(String(36))
    target_device_uuid = Column(String(36))
    timestamp = Column(DateTime())
    progress = Column(Integer())


class TaskStepRecord(Base):
    __tablename__ = "tasksteps"

    description = Column(String(256))
    easyucs_version = Column(String(100))
    name = Column(String(256))
    status = Column(String(16))
    status_message = Column(String(256))
    timestamp = Column(DateTime())
    timestamp_start = Column(DateTime())
    timestamp_stop = Column(DateTime())
    uuid = Column(String(36), nullable=False, primary_key=True)

    optional = Column(Boolean())
    order = Column(Integer())
    task_uuid = Column(String(36), nullable=False, primary_key=True)
    weight = Column(Integer())
