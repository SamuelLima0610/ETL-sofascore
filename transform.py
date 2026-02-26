from const import MATCH_OVER_VIEW, SHOTS, PASSES, DUELS, DEFENDING, GOALKEEPING

class Transform:

    def __init__(self, data):
        self.data = data

    def transform(self):
        transformed_data = []
        for game in self.data:
            if game['stats'] is not None:
                transformed_game = {
                    'season': game['season'],
                    'round': game['round'],
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'home_score': game['home_score'],
                    'away_score': game['away_score'],
                    'stats': self.transform_statistics_for_soccer_game(game['stats'])
                }
                transformed_data.append(transformed_game)
        return transformed_data
    
    def transform_statistics_for_soccer_game(self, statistics):
        transformed_statistics = {}
        for group in statistics:
            if group['groupName'] == 'Match overview':
                group['statisticsItems'] =  self.__get_statistics_by_group(group['statisticsItems'], MATCH_OVER_VIEW)
            elif group['groupName'] == 'Shots':
                group['statisticsItems'] =  self.__get_statistics_by_group(group['statisticsItems'], SHOTS)
            elif group['groupName'] == 'Passes':
                group['statisticsItems'] =  self.__get_statistics_by_group(group['statisticsItems'], PASSES)
            elif group['groupName'] == 'Duels': 
                group['statisticsItems'] =  self.__get_statistics_by_group(group['statisticsItems'], DUELS)
            elif group['groupName'] == 'Defending':
                group['statisticsItems'] =  self.__get_statistics_by_group(group['statisticsItems'], DEFENDING)
            elif group['groupName'] == 'Goalkeeping':
                group['statisticsItems'] =  self.__get_statistics_by_group(group['statisticsItems'], GOALKEEPING)
            transformed_statistics[group['groupName']] = group['statisticsItems']
        return transformed_statistics
    
    def __get_statistics_by_group(self, statistics, stat_list):
        # Chaves a manter por padrão (baseado na sua escolha)
        keep_keys = ['name', 'home', 'away', 'homeValue', 'awayValue']
        stats_to_keep = [stat for stat in statistics if stat['name'] in stat_list]
        statistics_desired = []
        for stat in stats_to_keep:
            filtered_stat = {}
            if stat.get('name') in stat_list:
                filtered = {k: stat[k] for k in keep_keys if k in stat}
                filtered_stat[stat.get('name')] = filtered
                statistics_desired.append(filtered_stat)
        return statistics_desired