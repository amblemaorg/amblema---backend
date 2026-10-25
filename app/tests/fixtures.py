# -*- coding: utf-8 -*-
# app/tests/fixtures.py
"""Datos de prueba reutilizables para las pruebas de integración."""

from datetime import datetime

from app.helpers.handler_seeds import create_standard_roles, create_initial_steps
from app.models.coordinator_user_model import CoordinatorUser
from app.models.role_model import Role
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear
from app.models.sponsor_user_model import SponsorUser
from app.models.state_model import State, Municipality


def create_location():
    state = State(name="Lara")
    state.save()
    municipality = Municipality(state=state, name="Iribarren")
    municipality.save()
    return state, municipality


def role(devName):
    return Role.objects(devName=devName).first()


def create_coordinator(state, municipality, email="coordinador@test.com", cardId="20000001",
                       firstName="Ana", lastName="Pérez"):
    coordinator = CoordinatorUser(
        firstName=firstName, lastName=lastName, cardType="1", cardId=cardId,
        birthdate=datetime(1990, 1, 1), gender="1", homePhone="02343432323",
        addressHome="Casa 1", email=email, password="12345678", userType="2",
        phone="02322322323", role=role("coordinator"), addressState=state,
        addressMunicipality=municipality, isReferred=False)
    coordinator.save()
    return coordinator


def create_sponsor(state, municipality, email="padrino@test.com", name="Empresa"):
    sponsor = SponsorUser(
        name=name, companyRif="303993833", companyType="2", companyPhone="02343432323",
        contactFirstName="Luis", contactLastName="Gómez", contactPhone="04244664646",
        addressHome="Calle 1", email=email, password="12345678", userType="3",
        role=role("sponsor"), addressState=state, addressMunicipality=municipality)
    sponsor.save()
    return sponsor


def create_school(state, municipality, email="escuela@test.com", code="0002", name="Escuela 1"):
    school = SchoolUser(
        name=name, code=code, phone="02343432323", schoolType="1",
        principalFirstName="Rosa", principalLastName="Díaz", principalEmail="directora@test.com",
        principalPhone="04244664646", nTeachers=20, nAdministrativeStaff=2, nLaborStaff=2,
        nStudents=200, nGrades=6, nSections=12, schoolShift="1", email=email,
        password="12345678", userType="4", role=role("school"), addressState=state,
        addressMunicipality=municipality)
    school.save()
    return school


def create_school_year(name="2025 - 2026", start=datetime(2025, 9, 1), end=datetime(2026, 7, 31),
                       status="1"):
    schoolYear = SchoolYear(name=name, startDate=start, endDate=end, status=status)
    schoolYear.initFirstPecaSetting()
    schoolYear.save()
    return schoolYear


def seed_base():
    """Roles estándar y pasos iniciales, necesarios para crear proyectos."""
    create_standard_roles()
    create_initial_steps()
