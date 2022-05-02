import pathlib
import subprocess
import hashlib
import csv
from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "TeDDi_sample"

    exampleTableProperties = ['text_raw', 'label', 'translation', 'segmentation', 'phonological', 'morphomic', 'footnote']
    valueTableProperties = ['language_name_wals', 'language_name_glotto', 'iso639_3', 'year_composed', 'year_published', 'mode', 'genre_broad', 'genre_narrow', 'writing_system', 'special_characters', 'short_description', 'source', 'copyright_short', 'copyright_long', 'sample_type', 'comments']
    contributionTableProperties = ['genre_broad', 'mode']
    languageTableProperties = ['wals_code', 'name_glotto', 'name_wals', 'level', 'status', 'family_id', 'top_level_family', 'genus_wals', 'family_wals', 'macroarea_wals', 'latitude_wals', 'longitude_wals', 'folder_language_name']

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(dir=self.cldf_dir, module='StructureDataset')

    def cmd_download(self, args):
        subprocess.check_call('git -C {} submodule update --remote'.format(self.dir.resolve()), shell=True)
        subprocess.check_call('cd ./raw/TeDDi_sample/Database/ && python load-database.py && Rscript sqlite_to_RData.R && Rscript to_csv.R', shell=True)

    def create_schema(self, ds):
        # examples.csv
        ds.add_component('ExampleTable')
        ds.remove_columns('ExampleTable', 'Analyzed_Word', 'Meta_Language_ID')
        ds.add_columns(
            'ExampleTable',
            {
                "dc:extent": "singlevalued",
                "datatype": "string",
                # "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#valueReference",
                "required": True,
                "name": "File_ID"
            },
            {
                "dc:extent": "singlevalued",
                "datatype": "string",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#contributionReference",
                "required": True,
                "name": "Corpus_ID"
            },
            *self.exampleTableProperties,
        )

        # values.csv
        ds.remove_columns('ValueTable', 'Code_ID', 'Source')
        ds.add_columns(
            'ValueTable',
            {
                "dc:extent": "singlevalued",
                "datatype": "string",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#contributionReference",
                "required": True,
                "name": "Corpus_ID"
            },
            *self.valueTableProperties,
        )

        ds.add_component('ParameterTable')

        # contributions.csv
        ds.add_component('ContributionTable')
        ds.remove_columns('ContributionTable', 'Description', 'Contributor', 'Citation')
        ds.add_columns(
            'ContributionTable',
            {'name': 'Language_ID', 'propertyUrl': "http://cldf.clld.org/v1.0/terms.rdf#languageReference"},
            *self.contributionTableProperties,
        )

        # languages.csv
        ds.add_component('LanguageTable', *self.languageTableProperties)

        ds.add_foreign_key('ExampleTable', 'File_ID', 'ValueTable', 'ID')
        ds.add_foreign_key('ExampleTable', 'Corpus_ID', 'ContributionTable', 'ID')
        ds.add_foreign_key('ExampleTable', 'Language_ID', 'LanguageTable', 'ID')
        ds.add_foreign_key('ValueTable', 'Corpus_ID', 'ContributionTable', 'ID')
        ds.add_foreign_key('ContributionTable', 'Language_ID', 'LanguageTable', 'ID')

    def cmd_makecldf(self, args):
        self.create_schema(args.writer.cldf)
            
        # languages.csv
        for row in self.raw_dir.read_csv(
            self.raw_dir / 'TeDDi_sample' / 'Database' / 'language.csv',
            dicts=True,
        ):
            args.writer.objects['LanguageTable'].append({
                'ID': row['id'],
                'Name': row['name'],
                'Glottocode': row['glottocode'],
                'ISO639P3code': row['iso639_3'],
                'Macroarea': row['macroarea_glotto'],
                'Latitude': row['latitude_glotto'],
                'Longitude': row['longitude_glotto'],
                **{ k: row[k] for k in self.languageTableProperties}
            })

        # contributions.csv
        for row in self.raw_dir.read_csv(
            self.raw_dir / 'TeDDi_sample' / 'Database' / 'corpus.csv',
            dicts=True,
        ):
            args.writer.objects['ContributionTable'].append({
                'ID': row['id'],
                'Name': row['name'],
                'Language_ID': row['language_id'],
                **{ k: row[k] for k in self.contributionTableProperties}
            })

        # values.csv
        for row in self.raw_dir.read_csv(
            self.raw_dir / 'TeDDi_sample' / 'Database' / 'file.csv',
            dicts=True,
        ):
            current_corpus = None
            for corpus in args.writer.objects['ContributionTable']:
                if corpus['ID'] == row['corpus_id']:
                    current_corpus = corpus

            args.writer.objects['ValueTable'].append({
                'ID': row['id'],
                'Value': row['filename'],
                'Corpus_ID': row['corpus_id'],
                'Language_ID': current_corpus['Language_ID'],
                'Parameter_ID': row['id'],
                **{ k: row[k] for k in self.valueTableProperties}
            })

            args.writer.objects['ParameterTable'].append({
                'ID': row['id'],
            })

        # examples.csv
        valueMap = {}
        for file in args.writer.objects['ValueTable']:
            valueMap[file['ID']] = file

        # WARNING: too large, won't fit into memory!
        # for idx, row in enumerate(self.raw_dir.read_csv(
        #     self.raw_dir / 'TeDDi_sample' / 'Database' / 'line.csv',
        #     dicts=True,
        # )):

        with open('{}/TeDDi_sample/Database/line.csv'.format(self.raw_dir), "r") as csvfile:
            datareader = csv.DictReader(csvfile)
            for row in datareader:
                current_file = valueMap[row['file_id']]

                args.writer.objects['ExampleTable'].append({
                    'ID': row['id'],
                    'Primary_Text': row['text'],
                    'Gloss': row['glossing'],
                    'File_ID': row['file_id'],
                    'Corpus_ID': current_file['Corpus_ID'],
                    'Language_ID': current_file['Language_ID'],
                    'Comment': row['comment'],
                    **{ k: row[k] for k in self.exampleTableProperties}
                })
