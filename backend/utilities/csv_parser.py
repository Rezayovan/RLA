import csv

# Returns two things:
# (1) candidate -> num_votes dictionary
# (2) num_total_votes for each office
def parse_election_data_csv(filename, office_to_return):
    # Need dict of office -> candidate (name_raw) -> votes
    data = {}
    offices = set()
    total_votes_per_office = {}
    with open(filename) as csv_file:
        reader = list(csv.DictReader(csv_file))

        for row in reader:
            offices.add(row["office"])

        if office_to_return not in offices:
            available_offices = ", ".join(offices)
            raise RuntimeError("Requested office is not available in the provided CSV. This CSV contains the following offices:", available_offices)

        data = dict.fromkeys(list(offices))

        # Create a new sub-dictionary for each office
        for key in data:
            data[key] = {}

        for row in reader:
            office = row["office"]
            name = row["name_raw"]
            votes = row["votes"]
            if name not in data[office]:
                data[office][name] = int(votes)
            else:
                data[office][name] += int(votes)

        total_votes_per_office = dict.fromkeys(list(offices), 0)

        for office, office_dict in data.items():
            for votes in office_dict.values():
                total_votes_per_office[office] += votes

    return data[office_to_return], total_votes_per_office

if __name__ == "__main__":
    print(parse_election_data_csv("open_election_test_data.csv", "State House")[0])
