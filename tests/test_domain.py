"""
Pruebas unitarias para los Value Objects (VO) del dominio.
"""
import unittest
from domain.value_objects import Year, GDP, Percentage, Population, LifeExpectancyYear, Source

class TestValueObjects(unittest.TestCase):

    def test_year_validation(self):
        # Años válidos
        self.assertEqual(Year(1900).value, 1900)
        self.assertEqual(Year(2023).value, 2023)
        self.assertEqual(Year(2100).value, 2100)

        # Años inválidos
        with self.assertRaises(ValueError):
            Year(1899)
        with self.assertRaises(ValueError):
            Year(2101)
        with self.assertRaises(TypeError):
            Year("abc")

    def test_gdp_validation(self):
        # PIB válido
        self.assertEqual(GDP(100.5).value, 100.5)

        # PIB inválido
        with self.assertRaises(ValueError):
            GDP(0)
        with self.assertRaises(ValueError):
            GDP(-100)
        with self.assertRaises(TypeError):
            GDP("abc")

    def test_percentage_validation(self):
        # Porcentaje válido
        self.assertEqual(Percentage(0).value, 0)
        self.assertEqual(Percentage(50.5).value, 50.5)
        self.assertEqual(Percentage(100).value, 100)

        # Porcentaje inválido
        with self.assertRaises(ValueError):
            Percentage(-0.1)
        with self.assertRaises(ValueError):
            Percentage(100.1)
        with self.assertRaises(TypeError):
            Percentage("abc")

    def test_population_validation(self):
        # Población válida
        self.assertEqual(Population(0).value, 0)
        self.assertEqual(Population(6000000).value, 6000000)

        # Población inválida
        with self.assertRaises(ValueError):
            Population(-1)
        with self.assertRaises(TypeError):
            Population("abc")

    def test_life_expectancy_validation(self):
        # Esperanza de vida válida
        self.assertEqual(LifeExpectancyYear(74.5).value, 74.5)

        # Esperanza de vida inválida
        with self.assertRaises(ValueError):
            LifeExpectancyYear(0)
        with self.assertRaises(ValueError):
            LifeExpectancyYear(-1.5)
        with self.assertRaises(TypeError):
            LifeExpectancyYear("abc")

    def test_source_validation(self):
        # Fuente válida
        self.assertEqual(Source("Banco Mundial").value, "Banco Mundial")
        self.assertEqual(Source("  FMI  ").value, "FMI")  # Trimmed

        # Fuente inválida
        with self.assertRaises(ValueError):
            Source("")
        with self.assertRaises(ValueError):
            Source("   ")
        with self.assertRaises(TypeError):
            Source(123)

    def test_immutability(self):
        # Los Value Objects deben ser inmutables
        y = Year(2020)
        with self.assertRaises(AttributeError):
            y.value = 2021

if __name__ == "__main__":
    unittest.main()
