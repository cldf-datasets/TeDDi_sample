import pathlib
import subprocess
import hashlib
from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "100LC"

    valueTableProperties = ['text_raw', 'label', 'text', 'translation', 'glossing', 'segmentation', 'phonological', 'morphomic', 'footnote']
    parameterTableProperties = ['language_name_wals', 'language_name_glotto', 'iso639_3', 'year_composed', 'year_published', 'mode', 'genre_broad', 'genre_narrow', 'writing_system', 'special_characters', 'short_description', 'source', 'copyright_short', 'copyright_long', 'sample_type', 'comments']
    contributionTableProperties = ['genre_broad', 'mode']
    languageTableProperties = ['wals_code', 'name_glotto', 'name_wals', 'level', 'status', 'family_id', 'top_level_family', 'genus_wals', 'family_wals', 'macroarea_wals', 'latitude_wals', 'longitude_wals', 'folder_language_name']

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(dir=self.cldf_dir, module='StructureDataset')

    def cmd_download(self, args):
        subprocess.check_call('git -C {} submodule update --remote'.format(self.dir.resolve()), shell=True)
        subprocess.check_call('cd ./raw/100LC/Database/ && python load-database.py -f && Rscript sqlite_to_RData.R && Rscript to_csv.R', shell=True)

    def create_schema(self, ds):
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

        # parameters.csv
        ds.add_component('ParameterTable')
        ds.remove_columns('ParameterTable', 'Description')
        ds.add_columns(
            'ParameterTable',
            {
                "dc:extent": "singlevalued",
                "datatype": "string",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#contributionReference",
                "required": True,
                "name": "Corpus_ID"
            },
            *self.parameterTableProperties,
        )

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

        ds.add_foreign_key('ValueTable', 'Corpus_ID', 'ContributionTable', 'ID')
        ds.add_foreign_key('ParameterTable', 'Corpus_ID', 'ContributionTable', 'ID')
        ds.add_foreign_key('ContributionTable', 'Language_ID', 'LanguageTable', 'ID')

    def cmd_makecldf(self, args):
        self.create_schema(args.writer.cldf)
            
        # languages.csv
        for row in self.raw_dir.read_csv(
            self.raw_dir / '100LC' / 'Database' / 'language.csv',
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
            self.raw_dir / '100LC' / 'Database' / 'corpus.csv',
            dicts=True,
        ):
            args.writer.objects['ContributionTable'].append({
                'ID': row['id'],
                'Name': row['name'],
                'Language_ID': row['language_id'],
                **{ k: row[k] for k in self.contributionTableProperties}
            })

        # parameters.csv
        for row in self.raw_dir.read_csv(
            self.raw_dir / '100LC' / 'Database' / 'file.csv',
            dicts=True,
        ):
            current_corpus = None
            for corpus in args.writer.objects['ContributionTable']:
                if corpus['ID'] == row['corpus_id']:
                    current_corpus = corpus

            args.writer.objects['ParameterTable'].append({
                'ID': row['id'],
                'Name': row['filename'],
                'Corpus_ID': row['corpus_id'],
                'Language_ID': current_corpus['Language_ID'],
                **{ k: row[k] for k in self.parameterTableProperties}
            })

        # values.csv
        for row in self.raw_dir.read_csv(
            self.raw_dir / '100LC' / 'Database' / 'line.csv',
            dicts=True,
        ):
            current_file = None
            for file in args.writer.objects['ParameterTable']:
                if file['ID'] == row['file_id']:
                    current_file = file

            args.writer.objects['ValueTable'].append({
                'ID': row['id'],
                'Value': row['text'],
                'Parameter_ID': row['file_id'],
                'Corpus_ID': current_file['Corpus_ID'],
                'Language_ID': current_file['Language_ID'],
                'Comment': row['comment'],
                **{ k: row[k] for k in self.valueTableProperties}
            })
