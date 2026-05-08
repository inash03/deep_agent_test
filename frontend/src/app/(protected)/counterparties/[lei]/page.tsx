import { CounterpartyEditPage } from '../../../../screens/CounterpartyEditPage'

type Props = {
  params: Promise<{ lei: string }>
}

export default async function Page({ params }: Props) {
  const { lei } = await params
  return <CounterpartyEditPage lei={lei} />
}
